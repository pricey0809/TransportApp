"""
Thin HTTP wrapper around the Valhalla routing API.

Routing calls live here; health checking stays in app.py (Stage 1).

Typical usage (Stage 4 wiring)::

    from valhalla.profiles import get_costing_options
    from valhalla.client import route, ValhallaError

    opts = get_costing_options(
        "BDOUBLE", 25.0, "hml",
        is_placard_load=True,
        dg_tunnel_flag="restricted",
    )
    result = route(
        locations=[
            {"lon": 153.0260, "lat": -27.4705},  # Brisbane
            {"lon": 151.2093, "lat": -33.8688},  # Sydney
        ],
        **opts,
    )
"""

import os

import requests


class ValhallaError(Exception):
    """Base class for all Valhalla client errors."""


class ValhallaHTTPError(ValhallaError):
    """Non-2xx HTTP response from Valhalla."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Valhalla returned HTTP {status_code}: {body[:200]}")


class ValhallaRouteError(ValhallaError):
    """Valhalla responded with HTTP 200 but returned an error payload."""

    def __init__(self, error_code: int, message: str) -> None:
        self.error_code = error_code
        self.message = message
        super().__init__(f"Valhalla routing error {error_code}: {message}")


def route(
    locations: list[dict],
    costing: str,
    costing_options: dict | None = None,
    avoid_polygons: list | None = None,
    *,
    units: str = "kilometres",
    directions_type: str = "instructions",
    language: str = "en-AU",
    timeout: int = 30,
) -> dict:
    """
    Call Valhalla's ``POST /route`` endpoint.

    Args:
        locations:
            List of location dicts. Each must have ``"lon"`` (float) and
            ``"lat"`` (float). Optionally include ``"type"`` — one of
            ``"break"`` (default), ``"through"``, ``"via"``, or
            ``"break_through"``.
        costing:
            Valhalla costing model. Use ``"truck"`` for heavy vehicles.
            Pass the value from profiles.get_costing_options()["costing"].
        costing_options:
            Dict of costing model options keyed by model name, e.g.
            ``{"truck": {"height": 4.3, ...}}``.
            Pass profiles.get_costing_options()["costing_options"] directly.
        avoid_polygons:
            Optional list of GeoJSON Polygon dicts to route around.
            Pass profiles.get_costing_options()["avoid_polygons"] directly,
            or None / empty list to skip. Used to route DG placard loads
            around restricted tunnels.
        units:
            ``"kilometres"`` (default) or ``"miles"``.
        directions_type:
            ``"maneuvers"`` (default), ``"instructions"``, or ``"none"``.
        timeout:
            HTTP request timeout in seconds. Default 30.

    Returns:
        The full parsed Valhalla route response dict.

    Raises:
        ValueError:                          Malformed location dict.
        requests.exceptions.ConnectionError: Valhalla is unreachable.
        requests.exceptions.Timeout:         Request timed out.
        ValhallaHTTPError:                   Non-2xx HTTP response.
        ValhallaRouteError:                  Valhalla error payload.
    """
    payload: dict = {
        "locations":       [_normalise_location(loc) for loc in locations],
        "costing":         costing,
        "units":           units,
        "directions_type": directions_type,
        "language":        language,
    }
    if costing_options:
        payload["costing_options"] = costing_options
    if avoid_polygons:
        payload["avoid_polygons"] = avoid_polygons

    valhalla_url = os.environ.get("VALHALLA_URL", "http://localhost:8002")
    resp = requests.post(
        f"{valhalla_url}/route",
        json=payload,
        timeout=timeout,
    )

    if not resp.ok:
        raise ValhallaHTTPError(resp.status_code, resp.text)

    body = resp.json()
    if "error" in body:
        raise ValhallaRouteError(
            body.get("error_code", -1),
            body.get("error", "Unknown Valhalla error"),
        )

    return body


# ── Internal helpers ──────────────────────────────────────────────────────────

def _normalise_location(loc: dict) -> dict:
    """
    Validate and normalise a location dict.

    Coerces lon/lat to float. Passes through an optional ``"type"`` field.
    Raises ValueError on missing or non-numeric coordinates.
    """
    try:
        lon = float(loc["lon"])
        lat = float(loc["lat"])
    except KeyError as exc:
        raise ValueError(f"Location missing required key: {exc}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Location lon/lat must be numeric: {exc}") from exc

    normalised: dict = {"lon": lon, "lat": lat}
    if "type" in loc:
        normalised["type"] = loc["type"]
    return normalised
