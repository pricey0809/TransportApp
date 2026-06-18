"""
Maps the three-step load configuration to Valhalla truck costing options.

nhvr/vehicles.py is the single source of truth for combination dimensions
and mass-scheme GVM ceilings.

Call pattern
────────────
Standard / CML / HML vehicle (most common):

    opts = get_costing_options(
        "BDOUBLE", 25.0, "hml",
        is_placard_load=True,          # sets hazmat flag
    )

PBS-approved vehicle (certified GVM overrides scheme table):

    opts = get_costing_options(
        "BDOUBLE", 25.0, "standard",
        is_pbs=True,
        manual_gvm_t=57.0,             # from the PBS Vehicle Approval document
    )

SPV — fully manual (all four dimension parameters required):

    opts = get_costing_options(
        "SPV_LCV", None, None,
        manual_dimensions={
            "length_m": 14.0,
            "width_m":   3.0,
            "height_m":  4.5,
            "gvm_t":    38.0,
            "axle_load_t": 9.0,        # optional
        },
    )

Oversize / Overmass (dimensions forwarded from the oversize permit form):

    opts = get_costing_options(
        "OVERSIZE", None, None,
        manual_dimensions={
            "length_m": form_length_m,
            "width_m":  form_width_m,
            "height_m": form_height_m,
            "gvm_t":    form_mass_t,    # gross mass = GVM
        },
    )

DG placard load + tunnel avoidance:

    opts = get_costing_options(
        "BDOUBLE", 25.0, "hml",
        is_placard_load=True,
        dg_tunnel_flag="restricted",   # from nhvr.dangerous_goods output
    )
    # opts["avoid_polygons"] → list of GeoJSON Polygon dicts for DG tunnels

Oversize permit — conservative routing:

    opts = get_costing_options(
        "OVERSIZE", None, None,
        manual_dimensions={...},
        permit_class="special",        # from nhvr.oversize.classify_permit()
    )
    # adds use_highways / use_ferry / use_tolls penalties to costing_options
"""

from nhvr.vehicles import COMBINATION_GROUPS, get_combination
from nhvr.tunnel_polygons import get_avoid_polygons

# ── Build flat lookups from COMBINATION_GROUPS ─────────────────────────────────

_MANUAL_DIM_CODES: frozenset[str] = frozenset(
    c["code"]
    for group in COMBINATION_GROUPS
    for c in group["combinations"]
    if c.get("requires_manual_dimensions")
)

_OVERSIZE_FORM_CODES: frozenset[str] = frozenset(
    c["code"]
    for group in COMBINATION_GROUPS
    for c in group["combinations"]
    if c.get("requires_oversize_form")
)


# ── Exceptions ────────────────────────────────────────────────────────────────

class ManualDimensionsRequired(ValueError):
    """
    Raised for SPV and OVERSIZE combinations when manual_dimensions was not
    supplied. Carries ``vehicle_code`` and a ``reason`` suitable for the UI.
    """
    def __init__(self, vehicle_code: str, reason: str) -> None:
        self.vehicle_code = vehicle_code
        self.reason = reason
        super().__init__(reason)


class PBSGVMRequired(ValueError):
    """
    Raised when ``is_pbs=True`` but ``manual_gvm_t`` was not supplied.
    PBS vehicles are individually certified — the GVM from the Vehicle
    Approval document must be used rather than a scheme table value.
    """
    def __init__(self, vehicle_code: str) -> None:
        self.vehicle_code = vehicle_code
        super().__init__(
            f"{vehicle_code} is PBS-approved: supply manual_gvm_t from the "
            "Vehicle Approval document."
        )


# ── Public API ────────────────────────────────────────────────────────────────

def get_costing_options(
    combination_code: str,
    length_m: float | None,
    mass_scheme: str | None,
    *,
    is_pbs: bool = False,
    manual_gvm_t: float | None = None,
    manual_dimensions: dict | None = None,
    is_placard_load: bool = False,
    dg_tunnel_flag: str = "none",
    permit_class: str = "none",
) -> dict:
    """
    Return a Valhalla costing block for the given load configuration.

    Args:
        combination_code:
            An NHVR combination code from nhvr.vehicles.COMBINATION_GROUPS.
        length_m:
            Overall vehicle length in metres. Must be one of the combination's
            declared lengths. Pass None for SPV / OVERSIZE (length comes from
            manual_dimensions instead).
        mass_scheme:
            ``"standard"``, ``"cml"``, or ``"hml"``. Must be a key in the
            combination's ``mass_schemes`` dict. Pass None for SPV / OVERSIZE.
        is_pbs:
            True when this vehicle holds a PBS Vehicle Approval. Forces use of
            ``manual_gvm_t`` instead of the scheme table value.
        manual_gvm_t:
            GVM in tonnes from the PBS Vehicle Approval document. Required when
            ``is_pbs=True``. Ignored otherwise.
        manual_dimensions:
            Required for SPV and OVERSIZE combinations.
            Keys:
                length_m     (float) — overall vehicle length in metres
                width_m      (float) — overall vehicle width in metres
                height_m     (float) — overall vehicle height in metres
                gvm_t        (float) — gross vehicle mass in tonnes
                axle_load_t  (float, optional) — max axle load in tonnes
            For OVERSIZE map the oversize form directly:
                gvm_t = form_mass_t   (gross mass equals GVM)
        is_placard_load:
            Pass ``is_placard_load`` from nhvr.dangerous_goods.classify_dg_load().
            When True, sets Valhalla's ``hazmat`` flag.
        dg_tunnel_flag:
            From nhvr.dangerous_goods output. One of ``"none"`` (default),
            ``"conditional"``, or ``"restricted"``. When not ``"none"`` and
            ``is_placard_load`` is True, populates ``avoid_polygons`` with
            curated DG-restricted tunnel geometries.

            ⚠️  Tunnel polygons are manually curated — not a live dataset.
            Verify against NHVR Route Planner before operational use.
        permit_class:
            From nhvr.oversize.classify_permit() output. One of ``"none"``
            (default), ``"class1"``, or ``"special"``. Adds conservative
            costing penalties for oversize / overmass loads:
              ``"class1"``  → use_highways: 0.5, use_ferry: 0.0
              ``"special"`` → use_highways: 0.2, use_ferry: 0.0, use_tolls: 0.3

    Returns:
        {
            "costing": "truck",
            "costing_options": {
                "truck": {
                    "length":       float,   # metres
                    "width":        float,   # metres
                    "height":       float,   # metres
                    "weight":       float,   # tonnes (GVM)
                    "axle_load":    float,   # tonnes (omitted when unknown)
                    "hazmat":       bool,
                    "use_highways": float,   # 0–1 (omitted unless oversize)
                    "use_ferry":    float,   # 0–1 (omitted unless oversize)
                    "use_tolls":    float,   # 0–1 (omitted for class1)
                }
            },
            "avoid_polygons": [...]  # list of GeoJSON Polygons; empty when no DG avoidance
        }

    Raises:
        KeyError:                 combination_code not found.
        ValueError:               length_m or mass_scheme invalid for combination.
        ManualDimensionsRequired: SPV / OVERSIZE called without manual_dimensions.
        PBSGVMRequired:           is_pbs=True but manual_gvm_t not supplied.
    """
    combo = get_combination(combination_code)
    if combo is None:
        raise KeyError(f"Unknown combination code: {combination_code!r}")

    # ── SPV: fully manual path ────────────────────────────────────────────────
    if combination_code in _MANUAL_DIM_CODES:
        if not manual_dimensions:
            raise ManualDimensionsRequired(
                combination_code,
                f"{combo['label']} is a Special Purpose Vehicle whose dimensions "
                "are non-standard by definition. Supply manual_dimensions with "
                "length_m, width_m, height_m, gvm_t, and optionally axle_load_t.",
            )
        return _build_block(
            manual_dimensions, is_placard_load, permit_class,
            dg_tunnel_flag if is_placard_load else "none",
        )

    # ── Oversize: dimensions from the oversize permit form ────────────────────
    if combination_code in _OVERSIZE_FORM_CODES:
        if not manual_dimensions:
            raise ManualDimensionsRequired(
                combination_code,
                "OVERSIZE requires dimensions from the oversize permit form. "
                "Supply manual_dimensions with width_m, height_m, length_m, "
                "and gvm_t (gross mass from the form).",
            )
        return _build_block(
            manual_dimensions, is_placard_load, permit_class,
            dg_tunnel_flag if is_placard_load else "none",
        )

    # ── Standard / CML / HML path ─────────────────────────────────────────────

    # Validate length
    valid_lengths = [l["length_m"] for l in combo.get("lengths", [])]
    if length_m not in valid_lengths:
        raise ValueError(
            f"length_m {length_m} is not valid for {combination_code!r}. "
            f"Valid lengths: {valid_lengths}"
        )

    # Validate mass scheme
    schemes = combo.get("mass_schemes", {})
    if mass_scheme not in schemes:
        raise ValueError(
            f"mass_scheme {mass_scheme!r} is not available for "
            f"{combination_code!r}. Available: {list(schemes)}"
        )

    scheme = schemes[mass_scheme]

    # PBS override
    if is_pbs:
        if manual_gvm_t is None:
            raise PBSGVMRequired(combination_code)
        gvm_t = float(manual_gvm_t)
    else:
        gvm_t = float(scheme["gvm_t"])

    dims = {
        "length_m":    length_m,
        "width_m":     combo["width_m"],
        "height_m":    combo["height_m"],
        "gvm_t":       gvm_t,
        "axle_load_t": scheme["axle_load_t"],
    }
    return _build_block(
        dims, is_placard_load, permit_class,
        dg_tunnel_flag if is_placard_load else "none",
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_block(
    dims: dict,
    is_placard_load: bool,
    permit_class: str = "none",
    dg_tunnel_flag: str = "none",
) -> dict:
    """Build the final Valhalla costing dict from a normalised dims dict."""
    truck: dict = {
        "length": float(dims["length_m"]),
        "width":  float(dims["width_m"]),
        "height": float(dims["height_m"]),
        "weight": float(dims["gvm_t"]),
        "hazmat": bool(is_placard_load),
    }
    axle = dims.get("axle_load_t")
    if axle is not None:
        truck["axle_load"] = float(axle)

    # Oversize / overmass permit → conservative routing preferences.
    # use_highways / use_ferry / use_tolls are 0–1 preference scores:
    #   1.0 = strongly preferred, 0.0 = strongly avoided
    if permit_class == "class1":
        # Within Class 1 permit maximums — avoid freeways where alternatives exist,
        # avoid ferries entirely (loading/unloading too risky for oversize).
        truck["use_highways"] = 0.5
        truck["use_ferry"]    = 0.0
    elif permit_class == "special":
        # Exceeds Class 1 limits — pilot / escort required; prefer lower-speed
        # roads, avoid tolled limited-access motorways where possible.
        truck["use_highways"] = 0.2
        truck["use_ferry"]    = 0.0
        truck["use_tolls"]    = 0.3

    result: dict = {"costing": "truck", "costing_options": {"truck": truck}}

    # DG placard load → avoid curated DG-restricted tunnels.
    # avoid_polygons is a top-level Valhalla param (not inside costing_options).
    result["avoid_polygons"] = get_avoid_polygons(dg_tunnel_flag)

    return result
