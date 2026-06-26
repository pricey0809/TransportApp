"""
NHVR vehicle combination types, mass-scheme lookup, and NHVR API code mapping.

Three-step load configuration model
────────────────────────────────────
1. Combination  — the regulatory / accreditation class the vehicle operates under
                  (e.g. "B-Double", "Road Train Type 1"). Operators may run a
                  different physical setup but be accredited as a standard
                  configuration for mass purposes.

2. Mass scheme  — Standard, CML (where gazetted for that combination), or HML.
                  Each scheme maps to fixed, gazetted GVM and axle-load ceilings.

3. PBS override — Any combination can additionally hold a PBS Vehicle Approval.
                  When it does, the approval document's certified GVM must be
                  used instead of the scheme table value — PBS vehicles are
                  individually certified and the table value must not be assumed.

Special cases
─────────────
  SPV (SPV_LCV, SPV_SPECIAL, SPV_AGRICULTURAL)
      Dimensions are non-standard by definition. All four Valhalla parameters
      (length, width, height, GVM) must be entered by the operator.

  OVERSIZE / OVERMASS
      Dimensions come from the oversize permit form at query time.

Mass values — NHVR "Common Heavy Freight Vehicle Configurations" (ref 201707-0577)
───────────────────────────────────────────────────────────────────────────────────
All GVM figures are the maximum for the most capable common axle configuration
in each category (i.e. the routing engine applies the heaviest legal scenario).

  Standard  — General Mass Limits (GML), HVNL Schedule 2
  CML       — Concessional Mass Limits (gazetted NHVR CML Notice)
  HML       — Higher Mass Limits (gazetted NHVR HML Notice; PBS axle-spacing
               compliance required, approved roads only)

  Road Train Type 1 = ≤ 36.5 m (canonical: 12-axle A-double, NHVR chart row 5c)
  Road Train Type 2 = ≤ 53.5 m (canonical: 18-axle A-triple, NHVR chart row 6b)

All widths are 2.5 m and heights 4.3 m (standard HVNL dimension limits).
"""

# ── Combination groups ─────────────────────────────────────────────────────────
#
# Each combination entry:
#   code                  str   — stable identifier used in API calls and profiles
#   label                 str   — display name
#   lengths               list  — [{length_m, label}]; single-element if no variant
#   default_length_m      float — pre-selected length in the UI (first if not set)
#   width_m               float — fixed outer width for this combination class
#   height_m              float — fixed outer height for this combination class
#   mass_schemes          dict  — {scheme_key: {label, gvm_t, axle_load_t}}
#                                 omitted for SPV / Oversize (manual only)
#   requires_manual_dimensions  bool — SPV: full manual input required
#   requires_oversize_form      bool — OVERSIZE: dimensions from oversize form

COMBINATION_GROUPS: list[dict] = [

    # ── B-Double ──────────────────────────────────────────────────────────────
    # NHVR chart section 4 — "Common B-Double Combinations – Class 2"
    # GVM figures: 9-axle B-double ≤ 26 m (row 4d) — the heaviest common config.
    {
        "group": "B-Double",
        "combinations": [
            {
                "code":             "BDOUBLE",
                "label":            "B-Double",
                "lengths": [
                    {"length_m": 19.0, "label": "19 m"},
                    {"length_m": 25.0, "label": "25 m"},
                    {"length_m": 26.0, "label": "26 m"},
                    {"length_m": 27.5, "label": "27.5 m (WA)"},
                ],
                "default_length_m": 25.0,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        62.5,
                        "axle_load_t":   9.0,
                    },
                    "cml": {
                        "label":        "Concessional Mass Limits (CML)",
                        "gvm_t":        64.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        68.0,
                        "axle_load_t":  10.0,
                    },
                },
            },
        ],
    },

    # ── Road Train ────────────────────────────────────────────────────────────
    # Type 1 = ≤ 36.5 m  (NHVR chart section 5, row 5c: 12-axle A-double)
    # Type 2 = ≤ 53.5 m  (NHVR chart section 6, row 6b: 18-axle A-triple)
    {
        "group": "Road Train",
        "combinations": [
            {
                "code":             "ROADTRAIN_T1",
                "label":            "Road Train Type 1",
                "lengths": [
                    {"length_m": 36.5, "label": "36.5 m"},
                ],
                "default_length_m": 36.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        82.5,
                        "axle_load_t":   9.0,
                    },
                    "cml": {
                        "label":        "Concessional Mass Limits (CML)",
                        "gvm_t":        84.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        90.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
            {
                "code":             "ROADTRAIN_T2",
                "label":            "Road Train Type 2",
                # Triple road train on gazetted routes (NT/WA/QLD remote only).
                "lengths": [
                    {"length_m": 53.5, "label": "53.5 m — gazetted remote routes only"},
                ],
                "default_length_m": 53.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":       122.5,
                        "axle_load_t":   9.0,
                    },
                    "cml": {
                        "label":        "Concessional Mass Limits (CML)",
                        "gvm_t":       124.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":       135.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
        ],
    },

    # ── A-Train / B-Train Combinations ────────────────────────────────────────
    # A-Double = canonical Type 1 road train (NHVR fact sheet fig. 15).
    # GVM figures: 12-axle A-double ≤ 36.5 m (NHVR chart row 5c) — same as T1.
    # B-Triple GVM: 12-axle B-triple ≤ 36.5 m (NHVR chart row 5e).
    {
        "group": "A-Train / B-Train Combinations",
        "combinations": [
            {
                "code":             "ADOUBLE",
                "label":            "A-Double",
                "lengths": [
                    {"length_m": 36.5, "label": "36.5 m"},
                ],
                "default_length_m": 36.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        82.5,
                        "axle_load_t":   9.0,
                    },
                    "cml": {
                        "label":        "Concessional Mass Limits (CML)",
                        "gvm_t":        84.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        90.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
            {
                "code":             "BTRIPLE",
                "label":            "B-Triple",
                "lengths": [
                    {"length_m": 36.5, "label": "36.5 m"},
                ],
                "default_length_m": 36.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        82.5,
                        "axle_load_t":   9.0,
                    },
                    "cml": {
                        "label":        "Concessional Mass Limits (CML)",
                        "gvm_t":        84.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        90.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
        ],
    },

    # ── Truck and Dog ─────────────────────────────────────────────────────────
    # GML 42.5 t is the HVNL Schedule 2 ceiling for all dog-trailer configs.
    # CML 43.5 t applies to dog trailer (not pig trailer) configurations.
    # HML does not apply to truck and dog (NHVR chart shows "—" in HML column).
    # NOTE: 22.5 m and 25 m lengths are State-access variants that exceed the
    # 19.0 m general access limit — they operate under specific State notices.
    {
        "group": "Truck and Dog",
        "combinations": [
            {
                "code":             "TRUCK_DOG",
                "label":            "Truck and Dog",
                "lengths": [
                    {"length_m": 22.5, "label": "22.5 m"},
                    {"length_m": 25.0, "label": "25 m"},
                ],
                "default_length_m": 22.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        42.5,
                        "axle_load_t":   9.0,
                    },
                    "cml": {
                        "label":        "Concessional Mass Limits (CML)",
                        "gvm_t":        43.5,
                        "axle_load_t":   9.0,
                    },
                },
            },
        ],
    },

    # ── Controlled Access Buses ───────────────────────────────────────────────
    # Class 2 CAB: rigid bus 12.5 m < L ≤ 14.5 m — GML 22.0 t (3-axle max,
    #   National Class 2 Bus Authorisation Notice 2024, NHVR bus chart items 15–16).
    # Articulated bus: L ≤ 18.0 m — GML 26.0 t (MDL / NHVR bus chart).
    {
        "group": "Controlled Access Buses",
        "combinations": [
            {
                "code":             "CAB_CLASS2",
                "label":            "Controlled Access Bus Class 2",
                "lengths": [
                    {"length_m": 14.5, "label": "14.5 m"},
                ],
                "default_length_m": 14.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        22.0,
                        "axle_load_t":   9.0,
                    },
                },
            },
            {
                "code":             "CAB_CLASS3",
                "label":            "Articulated Bus",
                # Articulated bus (Class 2) — MDL max length 18.0 m, GML 26.0 t.
                "lengths": [
                    {"length_m": 18.0, "label": "18 m"},
                ],
                "default_length_m": 18.0,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        26.0,
                        "axle_load_t":   9.0,
                    },
                },
            },
        ],
    },

    # ── Special Purpose Vehicles (Class 1) ────────────────────────────────────
    # Dimensions are non-standard by definition — full manual entry required.
    {
        "group": "Special Purpose Vehicles (Class 1)",
        "combinations": [
            {
                "code":   "SPV_LCV",
                "label":  "Load Carrying Vehicle (LCV)",
                "lengths":  [],
                "width_m":  None,
                "height_m": None,
                "mass_schemes": {},
                "requires_manual_dimensions": True,
            },
            {
                "code":   "SPV_SPECIAL",
                "label":  "Special Purpose Vehicle (SPV)",
                "lengths":  [],
                "width_m":  None,
                "height_m": None,
                "mass_schemes": {},
                "requires_manual_dimensions": True,
            },
            {
                "code":   "SPV_AGRICULTURAL",
                "label":  "Agricultural Heavy Vehicle",
                "lengths":  [],
                "width_m":  None,
                "height_m": None,
                "mass_schemes": {},
                "requires_manual_dimensions": True,
            },
        ],
    },

    # ── Oversize / Overmass ───────────────────────────────────────────────────
    # Dimensions captured by the oversize permit form at query time.
    {
        "group": "Oversize / Overmass",
        "combinations": [
            {
                "code":   "OVERSIZE",
                "label":  "Oversize / Overmass (Class 1)",
                "lengths":  [],
                "width_m":  None,
                "height_m": None,
                "mass_schemes": {},
                "requires_oversize_form": True,
            },
        ],
    },

]


# ── Flat combination lookup ────────────────────────────────────────────────────

_COMBO_BY_CODE: dict[str, dict] = {
    c["code"]: c
    for group in COMBINATION_GROUPS
    for c in group["combinations"]
}


def get_combination(code: str) -> dict | None:
    """Return the combination entry for a code, or None if not found."""
    return _COMBO_BY_CODE.get(code)


# ── NHVR API code mapping ─────────────────────────────────────────────────────
#
# Maps (combination_code, length_m, mass_scheme) → NHVR network API code.
#
# SPV / Oversize entries use (None, None) as they have no length or scheme.
# CML road trains reuse the standard network code — the NHVR network type
# identifier does not carry a separate CML designation.

_NHVR_CODE_MAP: dict[str, dict[tuple, str]] = {
    "BDOUBLE": {
        # 19 m fits within general access limits — no NHVR network permit needed.
        (19.0, "standard"): "GENERAL_ACCESS",
        (19.0, "cml"):      "GENERAL_ACCESS",
        (19.0, "hml"):      "GENERAL_ACCESS",
        (25.0, "standard"): "BDOUBLE_25M",
        (25.0, "cml"):      "BDOUBLE_25M",
        (25.0, "hml"):      "HML_BDOUBLE",
        (26.0, "standard"): "BDOUBLE_26M",
        (26.0, "cml"):      "BDOUBLE_26M",
        (26.0, "hml"):      "HML_BDOUBLE",
        # 27.5 m is WA-specific; use HML_BDOUBLE as the closest NHVR network code.
        (27.5, "standard"): "HML_BDOUBLE",
        (27.5, "cml"):      "HML_BDOUBLE",
        (27.5, "hml"):      "HML_BDOUBLE",
    },
    "ROADTRAIN_T1": {
        (36.5, "standard"): "ROADTRAIN_T1",
        (36.5, "cml"):      "ROADTRAIN_T1",
        (36.5, "hml"):      "HML_ROADTRAIN_T1",
    },
    "ROADTRAIN_T2": {
        (53.5, "standard"): "ROADTRAIN_T2_535M",
        (53.5, "cml"):      "ROADTRAIN_T2_535M",
        (53.5, "hml"):      "HML_ROADTRAIN_T2",
    },
    "ADOUBLE": {
        # No separate HML NHVR code for A-Double — same code regardless of scheme.
        (36.5, "standard"): "ADOUBLE_365M",
        (36.5, "cml"):      "ADOUBLE_365M",
        (36.5, "hml"):      "ADOUBLE_365M",
    },
    "BTRIPLE": {
        (36.5, "standard"): "BTRIPLE",
        (36.5, "cml"):      "BTRIPLE",
        (36.5, "hml"):      "BTRIPLE",
    },
    "TRUCK_DOG": {
        (22.5, "standard"): "TRUCK_DOG_225M",
        (22.5, "cml"):      "TRUCK_DOG_225M",
        (25.0, "standard"): "TRUCK_DOG_25M",
        (25.0, "cml"):      "TRUCK_DOG_25M",
    },
    "CAB_CLASS2": {
        (14.5, "standard"): "CAB_CLASS2",
    },
    "CAB_CLASS3": {
        (18.0, "standard"): "CAB_CLASS3",
    },
    "SPV_LCV":          {(None, None): "SPV_LOAD_CARRYING"},
    "SPV_SPECIAL":      {(None, None): "SPV_SPECIAL"},
    "SPV_AGRICULTURAL": {(None, None): "SPV_AGRICULTURAL"},
    "OVERSIZE":         {(None, None): "OVERSIZE_OVERMASS"},
}


def get_nhvr_code(
    combination_code: str,
    length_m: float | None,
    mass_scheme: str | None,
) -> str | None:
    """
    Return the NHVR API network-type code for a given combination + length + scheme.
    Returns None if no mapping exists.
    """
    inner = _NHVR_CODE_MAP.get(combination_code)
    if inner is None:
        return None
    return inner.get((length_m, mass_scheme))


# ── Backward-compatibility layer ──────────────────────────────────────────────
#
# nhvr/route.py uses get_vehicle_label(nhvr_code) and imports VEHICLE_CODES.
# Both are preserved so route.py needs no changes.

VEHICLE_CODES: dict[str, str] = {
    "GENERAL_ACCESS":    "General Access",
    "BDOUBLE_25M":       "B-Double 25m",
    "BDOUBLE_26M":       "B-Double 26m",
    "ROADTRAIN_T1":      "Road Train Type 1 (36.5m)",
    "ROADTRAIN_T2_535M": "Road Train Type 2 (53.5m)",
    "HML_BDOUBLE":       "HML B-Double",
    "HML_ROADTRAIN_T1":  "HML Road Train Type 1",
    "HML_ROADTRAIN_T2":  "HML Road Train Type 2",
    "ADOUBLE_365M":      "A-Double 36.5m",
    "BTRIPLE":           "B-Triple",
    "TRUCK_DOG_225M":    "Truck and Dog 22.5m",
    "TRUCK_DOG_25M":     "Truck and Dog 25m",
    "CAB_CLASS2":        "Controlled Access Bus Class 2",
    "CAB_CLASS3":        "Articulated Bus",
    "SPV_LOAD_CARRYING": "Load Carrying Vehicle (LCV)",
    "SPV_SPECIAL":       "Special Purpose Vehicle (SPV)",
    "SPV_AGRICULTURAL":  "Agricultural Heavy Vehicle",
    "OVERSIZE_OVERMASS": "Oversize / Overmass (Class 1)",
}


def get_vehicle_label(nhvr_code: str) -> str:
    """Look up the display label for an NHVR API vehicle/network code."""
    return VEHICLE_CODES.get(nhvr_code, nhvr_code)
