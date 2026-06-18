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

Mass values
───────────
  Standard  — HVNL Schedule 2 General Mass Limits
  CML       — Concessional Mass Limits (gazetted; currently defined for B-Double)
  HML       — Higher Mass Limits (NHVR CML Notice)

All widths are 2.5 m and heights 4.3 m (standard HVNL dimension limits).

The "Higher Mass Limits (HML)" group from the previous vehicle list is dissolved —
HML is now the "hml" mass scheme option within the relevant combination types.
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
    {
        "group": "B-Double",
        "combinations": [
            {
                "code":             "BDOUBLE",
                "label":            "B-Double",
                "lengths": [
                    {"length_m": 23.0, "label": "23 m"},
                    {"length_m": 25.0, "label": "25 m"},
                    {"length_m": 26.0, "label": "26 m"},
                ],
                "default_length_m": 25.0,
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
                        "gvm_t":        45.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        68.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
        ],
    },

    # ── Road Train ────────────────────────────────────────────────────────────
    {
        "group": "Road Train",
        "combinations": [
            {
                "code":             "ROADTRAIN_T1",
                "label":            "Road Train Type 1",
                "lengths": [
                    {"length_m": 26.5, "label": "26.5 m"},
                ],
                "default_length_m": 26.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        53.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        83.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
            {
                "code":             "ROADTRAIN_T2_36",
                "label":            "Road Train Type 2 (36.5 m)",
                "lengths": [
                    {"length_m": 36.5, "label": "36.5 m"},
                ],
                "default_length_m": 36.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        62.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":       105.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
            {
                "code":             "ROADTRAIN_T2_53",
                "label":            "Road Train Type 2 (53.5 m)",
                # Triple road train on gazetted NT/WA/QLD routes — Standard only.
                "lengths": [
                    {"length_m": 53.5, "label": "53.5 m — gazetted remote routes only"},
                ],
                "default_length_m": 53.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":       125.5,
                        "axle_load_t":   9.0,
                    },
                },
            },
        ],
    },

    # ── A-Train / B-Train Combinations ────────────────────────────────────────
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
                        "gvm_t":        53.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        68.5,
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
                        "gvm_t":        62.5,
                        "axle_load_t":   9.0,
                    },
                    "hml": {
                        "label":        "Higher Mass Limits (HML)",
                        "gvm_t":        68.5,
                        "axle_load_t":  10.0,
                    },
                },
            },
        ],
    },

    # ── Truck and Dog ─────────────────────────────────────────────────────────
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
                },
            },
        ],
    },

    # ── Controlled Access Buses ───────────────────────────────────────────────
    {
        "group": "Controlled Access Buses",
        "combinations": [
            {
                "code":             "CAB_CLASS2",
                "label":            "Controlled Access Bus Class 2",
                # Rigid bus exceeding standard access conditions; typically ≤14.5 m
                "lengths": [
                    {"length_m": 14.5, "label": "14.5 m"},
                ],
                "default_length_m": 14.5,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        20.0,
                        "axle_load_t":   9.0,
                    },
                },
            },
            {
                "code":             "CAB_CLASS3",
                "label":            "Controlled Access Bus Class 3",
                # Articulated bus; typical length 19 m
                "lengths": [
                    {"length_m": 19.0, "label": "19 m"},
                ],
                "default_length_m": 19.0,
                "width_m":  2.5,
                "height_m": 4.3,
                "mass_schemes": {
                    "standard": {
                        "label":        "Standard Mass",
                        "gvm_t":        28.0,
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
# CML B-doubles reuse the length-specific standard code because the NHVR
# network type identifier does not carry a separate CML designation.

_NHVR_CODE_MAP: dict[str, dict[tuple, str]] = {
    "BDOUBLE": {
        (23.0, "standard"): "BDOUBLE_23M",
        (23.0, "cml"):      "BDOUBLE_23M",
        (23.0, "hml"):      "HML_BDOUBLE",
        (25.0, "standard"): "BDOUBLE_25M",
        (25.0, "cml"):      "BDOUBLE_25M",
        (25.0, "hml"):      "HML_BDOUBLE",
        (26.0, "standard"): "BDOUBLE_26M",
        (26.0, "cml"):      "BDOUBLE_26M",
        (26.0, "hml"):      "HML_BDOUBLE",
    },
    "ROADTRAIN_T1": {
        (26.5, "standard"): "ROADTRAIN_T1_265M",
        (26.5, "hml"):      "HML_ROADTRAIN_T1",
    },
    "ROADTRAIN_T2_36": {
        (36.5, "standard"): "ROADTRAIN_T2_365M",
        (36.5, "hml"):      "HML_ROADTRAIN_T2",
    },
    "ROADTRAIN_T2_53": {
        (53.5, "standard"): "ROADTRAIN_T2_535M",
    },
    "ADOUBLE": {
        # No separate HML NHVR code for A-Double — same code regardless of scheme.
        (36.5, "standard"): "ADOUBLE_365M",
        (36.5, "hml"):      "ADOUBLE_365M",
    },
    "BTRIPLE": {
        (36.5, "standard"): "BTRIPLE",
        (36.5, "hml"):      "BTRIPLE",
    },
    "TRUCK_DOG": {
        (22.5, "standard"): "TRUCK_DOG_225M",
        (25.0, "standard"): "TRUCK_DOG_25M",
    },
    "CAB_CLASS2": {
        (14.5, "standard"): "CAB_CLASS2",
    },
    "CAB_CLASS3": {
        (19.0, "standard"): "CAB_CLASS3",
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
    "BDOUBLE_23M":       "B-Double 23m",
    "BDOUBLE_25M":       "B-Double 25m",
    "BDOUBLE_26M":       "B-Double 26m",
    "ROADTRAIN_T1_265M": "Road Train Type 1 (26.5m)",
    "ROADTRAIN_T2_365M": "Road Train Type 2 (36.5m)",
    "ROADTRAIN_T2_535M": "Road Train Type 2 (53.5m)",
    "HML_BDOUBLE":       "HML B-Double",
    "HML_ROADTRAIN_T1":  "HML Road Train Type 1",
    "HML_ROADTRAIN_T2":  "HML Road Train Type 2",
    "ADOUBLE_365M":      "A-Double 36.5m",
    "BTRIPLE":           "B-Triple",
    "TRUCK_DOG_225M":    "Truck and Dog 22.5m",
    "TRUCK_DOG_25M":     "Truck and Dog 25m",
    "CAB_CLASS2":        "Controlled Access Bus Class 2",
    "CAB_CLASS3":        "Controlled Access Bus Class 3",
    "SPV_LOAD_CARRYING": "Load Carrying Vehicle (LCV)",
    "SPV_SPECIAL":       "Special Purpose Vehicle (SPV)",
    "SPV_AGRICULTURAL":  "Agricultural Heavy Vehicle",
    "OVERSIZE_OVERMASS": "Oversize / Overmass (Class 1)",
}


def get_vehicle_label(nhvr_code: str) -> str:
    """Look up the display label for an NHVR API vehicle/network code."""
    return VEHICLE_CODES.get(nhvr_code, nhvr_code)
