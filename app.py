import os
import logging
from urllib.parse import urlencode

import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

from nhvr.client import NHVRClient, NHVRAuthError, NHVRAPIError
from nhvr.route import interpret_network_response
from nhvr.vehicles import COMBINATION_GROUPS, get_combination, get_nhvr_code
from nhvr.oversize import classify_permit
from nhvr.dangerous_goods import classify_dg_load, DG_CLASSES
from nhvr.tunnel_polygons import TUNNEL_POLYGONS
from valhalla.profiles import get_costing_options, ManualDimensionsRequired, PBSGVMRequired
from valhalla.client import route as valhalla_route, ValhallaError, ValhallaHTTPError, ValhallaRouteError
from valhalla.polyline import decode_shape

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _geocode(address: str) -> tuple[float, float] | None:
    """
    Geocode an address string to (lat, lon) using the Nominatim API.

    Restricted to Australia (countrycodes=au).  Returns None on any failure
    (bad address, network error, quota exceeded).
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "au"},
            headers={"User-Agent": "TransportApp/1.0 (heavy-vehicle-route-planner)"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None


def _build_route_maps_url(
    shape_coords: list[list[float]],
    origin_latlon: tuple[float, float],
    dest_latlon: tuple[float, float],
    n_waypoints: int = 6,
) -> str:
    """
    Build a Google Maps directions URL using actual route waypoints sampled
    from the Valhalla shape.

    ``shape_coords`` is a list of [lon, lat] pairs (GeoJSON order).
    Google Maps origin/destination/waypoints use lat,lon order.
    """
    origin_str = f"{origin_latlon[0]:.6f},{origin_latlon[1]:.6f}"
    dest_str   = f"{dest_latlon[0]:.6f},{dest_latlon[1]:.6f}"

    params: dict = {
        "api":        "1",
        "origin":     origin_str,
        "destination": dest_str,
        "travelmode": "driving",
    }

    if len(shape_coords) > 2:
        interior = shape_coords[1:-1]
        step     = max(1, len(interior) // n_waypoints)
        sampled  = interior[::step][:n_waypoints]
        if sampled:
            # shape_coords are [lon, lat]; Google Maps needs "lat,lon"
            params["waypoints"] = "|".join(
                f"{pt[1]:.6f},{pt[0]:.6f}" for pt in sampled
            )

    return "https://www.google.com/maps/dir/?" + urlencode(params)


# ── Views ─────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/")
def index():
    return render_template(
        "index.html",
        combination_groups=COMBINATION_GROUPS,
        dg_classes=DG_CLASSES,
    )


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/route", methods=["POST"])
def check_route():
    body = request.get_json(silent=True) or {}

    origin      = (body.get("origin")      or "").strip()
    destination = (body.get("destination") or "").strip()

    # ── Step 1: combination ───────────────────────────────────────────────────
    combination_code = (body.get("combination_code") or "").strip()

    # ── Step 2: length + mass scheme ─────────────────────────────────────────
    length_m_raw = body.get("length_m")
    mass_scheme  = (body.get("mass_scheme") or "").strip() or None

    # ── Step 3: PBS override ──────────────────────────────────────────────────
    is_pbs          = bool(body.get("is_pbs", False))
    manual_gvm_raw  = body.get("manual_gvm_t")

    # Manual dimensions (SPV / Oversize) — forwarded as-is, used in Stage 4
    manual_dimensions = body.get("manual_dimensions") or None

    errors: list[str] = []

    if not origin:
        errors.append("origin is required")
    if not destination:
        errors.append("destination is required")
    if not combination_code:
        errors.append("combination_code is required")

    combo = None
    if combination_code:
        combo = get_combination(combination_code)
        if combo is None:
            errors.append(f"unknown combination_code: {combination_code!r}")

    # Resolve length
    length_m: float | None = None
    if combo:
        valid_lengths = [l["length_m"] for l in combo.get("lengths", [])]
        is_manual = combo.get("requires_manual_dimensions") or combo.get("requires_oversize_form")

        if not is_manual:
            if len(valid_lengths) == 1:
                length_m = valid_lengths[0]
            elif length_m_raw is None:
                errors.append("length_m is required for this combination")
            else:
                try:
                    length_m = float(length_m_raw)
                    if length_m not in valid_lengths:
                        errors.append(
                            f"length_m {length_m} is not valid for "
                            f"{combination_code!r}; valid: {valid_lengths}"
                        )
                except (TypeError, ValueError):
                    errors.append("length_m must be a number")

    # Resolve mass scheme
    if combo and not combo.get("requires_manual_dimensions") and not combo.get("requires_oversize_form"):
        if not mass_scheme:
            errors.append("mass_scheme is required")
        elif mass_scheme not in combo.get("mass_schemes", {}):
            available = list(combo.get("mass_schemes", {}).keys())
            errors.append(
                f"mass_scheme {mass_scheme!r} is not available for "
                f"{combination_code!r}; available: {available}"
            )

    # Resolve PBS GVM
    manual_gvm_t: float | None = None
    if is_pbs:
        try:
            manual_gvm_t = float(manual_gvm_raw)
            if manual_gvm_t <= 0:
                errors.append("manual_gvm_t must be greater than zero")
        except (TypeError, ValueError):
            errors.append(
                "manual_gvm_t (certified PBS GVM in tonnes) is required when is_pbs is true"
            )

    # Validate manual_dimensions keys when present
    if manual_dimensions is not None and isinstance(manual_dimensions, dict):
        for key in ("length_m", "width_m", "height_m", "gvm_t"):
            if key not in manual_dimensions:
                errors.append(f"manual_dimensions.{key} is required")

    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    # ── Resolve NHVR code ─────────────────────────────────────────────────────
    is_manual = combo.get("requires_manual_dimensions") or combo.get("requires_oversize_form")
    if is_manual:
        nhvr_code = get_nhvr_code(combination_code, None, None)
    else:
        nhvr_code = get_nhvr_code(combination_code, length_m, mass_scheme)

    if nhvr_code is None:
        return jsonify({"error": "No NHVR network code found for this configuration."}), 400

    # Block OVERSIZE through the route endpoint
    if combo.get("requires_oversize_form"):
        return jsonify({"error": "Use /api/oversize for oversize / overmass queries."}), 400

    # ── NHVR network lookup ───────────────────────────────────────────────────
    try:
        nhvr_client = NHVRClient()
        networks = nhvr_client.find_networks(network_type=nhvr_code)
        if not networks:
            networks = nhvr_client.find_networks(network_name=nhvr_code)

    except NHVRAuthError as e:
        logger.error("NHVR auth error: %s", e)
        return jsonify({
            "error": "NHVR authentication failed. Check NHVR_API_KEY in .env."
        }), 502

    except NHVRAPIError as e:
        logger.error("NHVR API error: %s", e)
        if e.status_code == 404:
            return jsonify({
                "error": (
                    "NHVR Network endpoint not found. "
                    "Verify NHVR_API_BASE_URL is https://api-public.nhvr.gov.au"
                )
            }), 502
        return jsonify({"error": f"NHVR API error: {e}"}), 502

    except KeyError as e:
        return jsonify({
            "error": f"Missing environment variable: {e}. Check your .env file."
        }), 500

    except Exception as e:
        logger.exception("Unexpected error calling NHVR API")
        return jsonify({"error": f"Unexpected error: {e}"}), 500

    # ── Build vehicle label for the results summary ───────────────────────────
    parts = [combo["label"]]

    if length_m is not None:
        parts.append(f"{length_m:g} m")

    if mass_scheme and mass_scheme in combo.get("mass_schemes", {}):
        scheme_data = combo["mass_schemes"][mass_scheme]
        effective_gvm = manual_gvm_t if is_pbs else scheme_data["gvm_t"]
        parts.append(scheme_data["label"])
        parts.append(f"{effective_gvm:g} t GVM" + (" — PBS" if is_pbs else ""))

    vehicle_label = " — ".join(parts)

    result = interpret_network_response(
        networks, nhvr_code, origin, destination,
        vehicle_label=vehicle_label,
    )
    return jsonify(result.to_dict())


# ── Oversize / Overmass permit check ─────────────────────────────────────────

@app.route("/api/oversize", methods=["POST"])
def check_oversize():
    body = request.get_json(silent=True) or {}

    errors = []

    def _float(key: str, label: str):
        val = body.get(key)
        try:
            f = float(val)
            if f <= 0:
                errors.append(f"{label} must be greater than zero")
            return f
        except (TypeError, ValueError):
            errors.append(f"{label} is required and must be a number")
            return None

    width_m  = _float("width_m",  "Width")
    height_m = _float("height_m", "Height")
    length_m = _float("length_m", "Length")
    mass_t   = _float("mass_t",   "Gross mass")

    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    result = classify_permit(width_m, height_m, length_m, mass_t)
    return jsonify(result)


# ── Dangerous goods placard load check ───────────────────────────────────────

@app.route("/api/dangerous-goods", methods=["POST"])
def check_dangerous_goods():
    body = request.get_json(silent=True) or {}

    errors = []

    dg_class = (body.get("dg_class") or "").strip()
    un_number = (body.get("un_number") or "").strip()
    packing_group = (body.get("packing_group") or "").strip() or None

    if not dg_class:
        errors.append("dg_class is required")

    try:
        quantity = float(body.get("quantity", 0))
        if quantity <= 0:
            errors.append("quantity must be greater than zero")
    except (TypeError, ValueError):
        errors.append("quantity is required and must be a number")
        quantity = 0.0

    if un_number and (not un_number.isdigit() or len(un_number) != 4):
        errors.append("UN number must be exactly 4 digits")

    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    result = classify_dg_load(dg_class, un_number, quantity, packing_group)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


# ── Shared Valhalla setup helper ──────────────────────────────────────────────

def _prepare_valhalla_context(body: dict):
    """
    Validate request, geocode addresses, classify DG/oversize loads, and build
    Valhalla costing options.  Shared by /api/route-geometry and /api/valhalla-params.

    Returns:
        (ctx_dict, None)            on success
        (None, (error_dict, code))  on validation/geocoding failure — caller
                                    should ``return jsonify(error_dict), code``
    """
    origin           = (body.get("origin")           or "").strip()
    destination      = (body.get("destination")      or "").strip()
    combination_code = (body.get("combination_code") or "").strip()

    if not origin:
        return None, ({"error": "origin is required"}, 400)
    if not destination:
        return None, ({"error": "destination is required"}, 400)
    if not combination_code:
        return None, ({"error": "combination_code is required"}, 400)

    combo = get_combination(combination_code)
    if combo is None:
        return None, ({"error": f"Unknown combination_code: {combination_code!r}"}, 400)

    length_m_raw      = body.get("length_m")
    mass_scheme       = (body.get("mass_scheme") or "").strip() or None
    is_pbs            = bool(body.get("is_pbs", False))
    manual_gvm_raw    = body.get("manual_gvm_t")
    manual_dimensions = body.get("manual_dimensions") or None
    is_manual         = combo.get("requires_manual_dimensions") or combo.get("requires_oversize_form")

    length_m: float | None = None
    if not is_manual:
        valid_lengths = [l["length_m"] for l in combo.get("lengths", [])]
        if len(valid_lengths) == 1:
            length_m = valid_lengths[0]
        elif length_m_raw is not None:
            try:
                length_m = float(length_m_raw)
            except (TypeError, ValueError):
                return None, ({"error": "length_m must be a number"}, 400)

    manual_gvm_t: float | None = None
    if is_pbs:
        try:
            manual_gvm_t = float(manual_gvm_raw)
        except (TypeError, ValueError):
            return None, ({"error": "manual_gvm_t is required when is_pbs is true"}, 400)

    # DG classification
    is_placard_load = False
    dg_tunnel_flag  = "none"
    dg_class = (body.get("dg_class") or "").strip()
    if dg_class:
        try:
            dg_quantity = float(body.get("dg_quantity", 0))
        except (TypeError, ValueError):
            dg_quantity = 0.0
        dg_result = classify_dg_load(
            dg_class,
            un_number     = (body.get("dg_un_number") or "").strip(),
            quantity      = dg_quantity,
            packing_group = body.get("dg_packing_group") or None,
        )
        if "error" not in dg_result:
            is_placard_load = bool(dg_result.get("is_placard_load", False))
            dg_tunnel_flag  = dg_result.get("tunnel_flag", "none")

    # Oversize permit classification
    permit_class = "none"
    if is_manual and isinstance(manual_dimensions, dict):
        try:
            oversize_result = classify_permit(
                width_m  = float(manual_dimensions.get("width_m",  0)),
                height_m = float(manual_dimensions.get("height_m", 0)),
                length_m = float(manual_dimensions.get("length_m", 0)),
                mass_t   = float(manual_dimensions.get("gvm_t",    0)),
            )
            permit_class = oversize_result.get("permit_class", "none")
        except (TypeError, ValueError):
            pass

    # Geocode
    origin_latlon = _geocode(origin)
    dest_latlon   = _geocode(destination)
    if origin_latlon is None:
        return None, ({"error": (
            f"Could not geocode origin {origin!r}. "
            "Try a more specific Australian address (e.g. 'Brisbane QLD' or '1 George St Sydney NSW')."
        )}, 400)
    if dest_latlon is None:
        return None, ({"error": (
            f"Could not geocode destination {destination!r}. "
            "Try a more specific Australian address."
        )}, 400)

    # Costing options
    try:
        costing_opts = get_costing_options(
            combination_code, length_m, mass_scheme,
            is_pbs            = is_pbs,
            manual_gvm_t      = manual_gvm_t,
            manual_dimensions = manual_dimensions,
            is_placard_load   = is_placard_load,
            dg_tunnel_flag    = dg_tunnel_flag,
            permit_class      = permit_class,
        )
    except (ManualDimensionsRequired, PBSGVMRequired, KeyError, ValueError) as e:
        return None, ({"error": str(e)}, 400)

    # Tunnels avoided (derived from costing options)
    avoid_polygons_sent = costing_opts.get("avoid_polygons", [])
    if not avoid_polygons_sent:
        tunnels_avoided: list[dict] = []
    elif dg_tunnel_flag == "restricted":
        tunnels_avoided = [
            {"name": t["name"], "state": t["state"],
             "restriction_level": t["restriction_level"], "polygon": t["polygon"]}
            for t in TUNNEL_POLYGONS if t["restriction_level"] == "restricted"
        ]
    else:
        tunnels_avoided = [
            {"name": t["name"], "state": t["state"],
             "restriction_level": t["restriction_level"], "polygon": t["polygon"]}
            for t in TUNNEL_POLYGONS
        ]

    # Vehicle label
    parts = [combo["label"]]
    if length_m is not None:
        parts.append(f"{length_m:g} m")
    if mass_scheme and mass_scheme in combo.get("mass_schemes", {}):
        scheme_data   = combo["mass_schemes"][mass_scheme]
        effective_gvm = manual_gvm_t if is_pbs else scheme_data["gvm_t"]
        parts.append(scheme_data["label"])
        parts.append(f"{effective_gvm:g} t GVM" + (" — PBS" if is_pbs else ""))
    vehicle_label = " — ".join(parts)

    return {
        "origin":           origin,
        "destination":      destination,
        "origin_latlon":    origin_latlon,
        "dest_latlon":      dest_latlon,
        "costing_opts":     costing_opts,
        "tunnels_avoided":  tunnels_avoided,
        "vehicle_label":    vehicle_label,
        "is_placard_load":  is_placard_load,
        "permit_class":     permit_class,
    }, None


# ── Valhalla route geometry ───────────────────────────────────────────────────

@app.route("/api/valhalla-params", methods=["POST"])
def valhalla_params():
    """
    Return geocoded coordinates and a pre-built Valhalla /route request body
    for the browser to call Valhalla directly.

    This sidesteps server-to-server blocks on public Valhalla instances (which
    return 405 for non-browser requests) while keeping geocoding and costing
    logic server-side.

    Returns:
        {
          "valhalla_url":     URL the browser should POST to,
          "valhalla_request": complete Valhalla /route request body,
          "origin":           { lat, lon, label },
          "destination":      { lat, lon, label },
          "vehicle_label":    human-readable vehicle description,
          "tunnels_avoided":  [ { name, state, restriction_level, polygon }, ... ],
          "is_placard_load":  bool,
          "permit_class":     str,
        }
    """
    body = request.get_json(silent=True) or {}
    ctx, err = _prepare_valhalla_context(body)
    if err:
        return jsonify(err[0]), err[1]

    valhalla_url = os.environ.get("VALHALLA_URL", "http://localhost:8002")

    valhalla_request: dict = {
        "locations": [
            {"lon": ctx["origin_latlon"][1], "lat": ctx["origin_latlon"][0]},
            {"lon": ctx["dest_latlon"][1],   "lat": ctx["dest_latlon"][0]},
        ],
        "costing":         ctx["costing_opts"]["costing"],
        "units":           "kilometres",
        "directions_type": "instructions",
        "language":        "en-AU",
    }
    if ctx["costing_opts"].get("costing_options"):
        valhalla_request["costing_options"] = ctx["costing_opts"]["costing_options"]
    if ctx["costing_opts"].get("avoid_polygons"):
        valhalla_request["avoid_polygons"] = ctx["costing_opts"]["avoid_polygons"]

    return jsonify({
        "valhalla_url":     valhalla_url,
        "valhalla_request": valhalla_request,
        "origin":      {"lat": ctx["origin_latlon"][0], "lon": ctx["origin_latlon"][1], "label": ctx["origin"]},
        "destination": {"lat": ctx["dest_latlon"][0],   "lon": ctx["dest_latlon"][1],   "label": ctx["destination"]},
        "vehicle_label":   ctx["vehicle_label"],
        "tunnels_avoided": ctx["tunnels_avoided"],
        "is_placard_load": ctx["is_placard_load"],
        "permit_class":    ctx["permit_class"],
    })


@app.route("/api/proxy/valhalla", methods=["POST"])
def proxy_valhalla():
    """
    Thin proxy: forwards the browser's pre-built Valhalla request to the
    routing engine with a browser-like User-Agent.

    Solves two problems simultaneously:
    - CORS: browser POSTs here (same origin) instead of cross-origin to Valhalla
    - 405: public Valhalla (valhalla.openstreetmap.de) blocks python-requests
            User-Agent; this sends a browser UA instead
    """
    valhalla_url = os.environ.get("VALHALLA_URL", "http://localhost:8002")
    raw_body = request.get_data()
    try:
        resp = requests.post(
            f"{valhalla_url}/route",
            data=raw_body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-AU,en;q=0.9",
                "Origin": valhalla_url,
                "Referer": valhalla_url + "/",
            },
            timeout=30,
        )
        if not resp.ok:
            # Valhalla returned an error — extract text and return clean JSON
            # (never forward raw HTML pages to the browser)
            try:
                err_body = resp.json()
                err_msg = err_body.get("error", {}).get("description") or str(err_body)
            except Exception:
                err_msg = resp.text[:300] or f"HTTP {resp.status_code}"
            return jsonify({"error": f"Valhalla returned HTTP {resp.status_code}: {err_msg}"}), resp.status_code
        return resp.content, resp.status_code, {"Content-Type": "application/json"}
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Routing engine not available"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Routing engine timed out"}), 503
    except Exception as e:
        logger.exception("Valhalla proxy error")
        return jsonify({"error": f"Proxy error: {e}"}), 500


@app.route("/api/route-geometry", methods=["POST"])
def route_geometry():
    """
    Calculate an actual truck route via Valhalla server-side and return GeoJSON.
    Kept for local development where Valhalla runs on localhost.
    For cloud deployments use /api/valhalla-params + /api/proxy/valhalla.
    """
    body = request.get_json(silent=True) or {}
    ctx, err = _prepare_valhalla_context(body)
    if err:
        return jsonify(err[0]), err[1]

    # ── Call Valhalla /route ──────────────────────────────────────────────────
    try:
        vr = valhalla_route(
            locations = [
                {"lon": ctx["origin_latlon"][1], "lat": ctx["origin_latlon"][0]},
                {"lon": ctx["dest_latlon"][1],   "lat": ctx["dest_latlon"][0]},
            ],
            costing         = ctx["costing_opts"]["costing"],
            costing_options = ctx["costing_opts"].get("costing_options"),
            avoid_polygons  = ctx["costing_opts"].get("avoid_polygons") or None,
        )
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Routing engine not available. Run: docker compose up -d valhalla"
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Routing engine timed out — tiles may still be building."}), 503
    except ValhallaRouteError as e:
        # Error 442 = "No path could be found" — most commonly triggered by a
        # height/weight/dimension restriction blocking all available paths.
        if e.error_code == 442:
            logger.warning("Valhalla 442 (no path): %s", e.message)
            return jsonify({
                "error": (
                    "No legal route found \u2014 the only path between these points is "
                    "height-restricted for this vehicle. Check posted bridge and tunnel "
                    "clearance signs and consider an alternative start or end point."
                ),
                "error_type": "height_restricted",
            }), 400
        logger.error("Valhalla route error: %s", e)
        return jsonify({"error": f"Routing error: {e}"}), 502
    except ValhallaHTTPError as e:
        logger.error("Valhalla HTTP error: %s", e)
        return jsonify({"error": f"Routing engine error: {e}"}), 502
    except ValhallaError as e:
        logger.error("Valhalla error: %s", e)
        return jsonify({"error": f"Routing error: {e}"}), 502
    except Exception as e:
        logger.exception("Unexpected error calling Valhalla")
        return jsonify({"error": f"Unexpected routing error: {e}"}), 500

    # ── Decode shape and collect maneuvers ────────────────────────────────────────
    shape_coords: list[list[float]] = []
    all_maneuvers: list[dict] = []
    shape_offset = 0

    trip = vr.get("trip", {})
    for leg in trip.get("legs", []):
        leg_coords = decode_shape(leg["shape"])
        for m in leg.get("maneuvers", []):
            all_maneuvers.append({
                "type":              m.get("type", 0),
                "instruction":       m.get("instruction", ""),
                "verbal_pre":        m.get("verbal_pre_transition_instruction", ""),
                "verbal_alert":      m.get("verbal_transition_alert_instruction", ""),
                "street_names":      m.get("street_names", []),
                "length":            round(m.get("length", 0), 3),
                "time":              round(m.get("time", 0)),
                "begin_shape_index": m.get("begin_shape_index", 0) + shape_offset,
                "end_shape_index":   m.get("end_shape_index", 0) + shape_offset,
            })
        shape_coords.extend(leg_coords)
        shape_offset += len(leg_coords)

    distance_km  = round(trip.get("summary", {}).get("length", 0), 1)
    duration_min = round(trip.get("summary", {}).get("time",   0) / 60)

    maps_url = _build_route_maps_url(shape_coords, ctx["origin_latlon"], ctx["dest_latlon"])

    return jsonify({
        "route": {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": shape_coords},
                "properties": {
                    "distance_km":           distance_km,
                    "duration_min":          duration_min,
                    "vehicle_label":         ctx["vehicle_label"],
                    "is_placard_load":       ctx["is_placard_load"],
                    "permit_class":          ctx["permit_class"],
                    "tunnels_avoided_count": len(ctx["tunnels_avoided"]),
                },
            }],
        },
        "summary": {
            "distance_km":  distance_km,
            "duration_min": duration_min,
            "origin":       {"lat": ctx["origin_latlon"][0], "lon": ctx["origin_latlon"][1], "label": ctx["origin"]},
            "destination":  {"lat": ctx["dest_latlon"][0],   "lon": ctx["dest_latlon"][1],   "label": ctx["destination"]},
            "vehicle_label": ctx["vehicle_label"],
        },
        "tunnels_avoided": ctx["tunnels_avoided"],
        "maps_url":    maps_url,
        "maneuvers":   all_maneuvers,
    })


# ── Valhalla routing engine — health check ───────────────────────────────────

@app.route("/api/valhalla/status")
def valhalla_status():
    """
    Proxy Valhalla's /status endpoint so the frontend can check whether the
    self-hosted routing engine is up without being blocked by CORS.
    """
    valhalla_url = os.environ.get("VALHALLA_URL", "http://localhost:8002")
    try:
        resp = requests.get(f"{valhalla_url}/status", timeout=5)
        resp.raise_for_status()
        return jsonify({
            "status":  "up",
            "url":     valhalla_url,
            "detail":  resp.json(),
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            "status":  "down",
            "url":     valhalla_url,
            "error":   (
                "Cannot reach Valhalla. "
                "Run: docker compose up -d valhalla"
            ),
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "down",
            "url":    valhalla_url,
            "error":  "Valhalla health check timed out (tiles may still be building).",
        }), 503
    except Exception as e:
        return jsonify({"status": "down", "url": valhalla_url, "error": str(e)}), 503


# ── Google Maps URL helper ────────────────────────────────────────────────────

@app.route("/api/maps-url")
def maps_url():
    origin      = request.args.get("origin", "")
    destination = request.args.get("destination", "")
    params = urlencode({
        "api":         "1",
        "origin":      origin,
        "destination": destination,
        "travelmode":  "driving",
    })
    return jsonify({"url": f"https://www.google.com/maps/dir/?{params}"})


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=5000)
