"""
NHVR oversize/overmass permit classification and state-specific restrictions.

Thresholds are based on NHVR Class 1 permit conditions under the Heavy Vehicle
National Law (HVNL). Always verify with NHVR and the relevant state road authority
before travel.

Reference: https://www.nhvr.gov.au/road-access/oversize-overmass
"""

# Standard dimension limits — no permit required below these thresholds
STANDARD_LIMITS = {
    "width_m":  2.5,
    "height_m": 4.3,
    "length_m": 19.0,   # general articulated combination
    "mass_t":   42.5,   # General Mass Limit (GML) for a typical 6-axle semi
}

# Class 1 permit maximums — beyond these requires a special assessment
CLASS1_MAX = {
    "width_m":  5.0,
    "height_m": 5.0,
    "length_m": 36.5,
}

# Per-state oversize rules
_STATE_RULES = {
    "NSW": {
        "pilot_width_m":  3.5,
        "escort_width_m": 5.0,
        "max_width_m":    5.0,
        "travel_note": (
            "Night travel not permitted between 7 pm – 7 am "
            "on most roads without special approval."
        ),
        "extra": [
            "Time-of-day curfews apply in the Sydney metropolitan area.",
            "Bridge clearances vary — verify with Transport for NSW before travel.",
        ],
    },
    "VIC": {
        "pilot_width_m":  3.5,
        "escort_width_m": 5.0,
        "max_width_m":    5.0,
        "travel_note": (
            "Movement not permitted between sunset and sunrise "
            "without special approval."
        ),
        "extra": [
            "Melbourne CBD has strict curfew restrictions for oversize loads.",
            "VicRoads route assessment required for loads wider than 4.9 m.",
        ],
    },
    "QLD": {
        "pilot_width_m":  3.5,
        "escort_width_m": 5.0,
        "max_width_m":    5.5,
        "travel_note": "Night travel restrictions apply on declared roads.",
        "extra": [
            "Police or traffic controller escort required for width > 5.0 m.",
            "Gazetted routes required for loads exceeding Class 1 maximums.",
        ],
    },
    "WA": {
        "pilot_width_m":  3.5,
        "escort_width_m": 4.5,
        "max_width_m":    6.0,
        "travel_note": (
            "Night travel permitted on some remote routes with approval."
        ),
        "extra": [
            "Escort required from 4.5 m width on Perth metropolitan roads.",
            "Remote/Outback roads may have different limits — check Main Roads WA.",
        ],
    },
    "SA": {
        "pilot_width_m":  3.5,
        "escort_width_m": 5.0,
        "max_width_m":    5.0,
        "travel_note": "Night movement generally prohibited without special permit.",
        "extra": [
            "Contact DPTI for loads exceeding 5.0 m wide.",
        ],
    },
    "TAS": {
        "pilot_width_m":  3.0,
        "escort_width_m": 4.5,
        "max_width_m":    4.5,
        "travel_note": "Night movement not permitted without special approval.",
        "extra": [
            "Tasmania has more restrictive width limits due to narrower road geometry.",
            "Many state road bridges have lower height clearances than mainland averages.",
            "Infrastructure Tasmania approval required for loads wider than 4.5 m.",
        ],
    },
    "NT": {
        "pilot_width_m":  3.5,
        "escort_width_m": 5.0,
        "max_width_m":    6.0,
        "travel_note": (
            "Night movement permitted on some Stuart Highway corridors."
        ),
        "extra": [
            "Wet season road closures may apply (October – April).",
            "NT road train routes are more permissive for length limits.",
        ],
    },
    "ACT": {
        "pilot_width_m":  3.0,
        "escort_width_m": 4.5,
        "max_width_m":    4.5,
        "travel_note": (
            "No oversize movement during peak hours (7–9 am and 4–6 pm)."
        ),
        "extra": [
            "Most oversize routes through ACT must be pre-approved by Transport Canberra.",
            "Loads wider than 4.5 m require special assessment.",
        ],
    },
}


def classify_permit(
    width_m: float,
    height_m: float,
    length_m: float,
    mass_t: float,
) -> dict:
    """
    Determine NHVR permit class and state-specific restrictions for the given dimensions.

    Returns a dict with:
      permit_class        — "none" | "class1" | "special"
      permit_description  — human-readable summary
      exceedances         — which standard limits are exceeded
      requires_pilot      — states requiring a pilot vehicle for this width
      requires_escort     — states requiring police/traffic escort for this width
      state_flags         — per-state restriction messages  {state: [str, ...]}
      beyond_class1       — True if any dimension exceeds Class 1 maximums
    """
    exceedances: list[str] = []

    if width_m > STANDARD_LIMITS["width_m"]:
        exceedances.append(
            f"Width {width_m:.2f} m exceeds standard limit of "
            f"{STANDARD_LIMITS['width_m']} m"
        )
    if height_m > STANDARD_LIMITS["height_m"]:
        exceedances.append(
            f"Height {height_m:.2f} m exceeds standard limit of "
            f"{STANDARD_LIMITS['height_m']} m"
        )
    if length_m > STANDARD_LIMITS["length_m"]:
        exceedances.append(
            f"Length {length_m:.1f} m exceeds standard limit of "
            f"{STANDARD_LIMITS['length_m']} m"
        )
    if mass_t > STANDARD_LIMITS["mass_t"]:
        exceedances.append(
            f"Gross mass {mass_t:.1f} t exceeds General Mass Limit of "
            f"{STANDARD_LIMITS['mass_t']} t"
        )

    if not exceedances:
        return {
            "permit_class": "none",
            "permit_description": (
                "No permit required — all dimensions are within standard Australian road limits."
            ),
            "exceedances": [],
            "requires_pilot": [],
            "requires_escort": [],
            "state_flags": {},
            "beyond_class1": False,
        }

    beyond_class1 = (
        width_m  > CLASS1_MAX["width_m"]  or
        height_m > CLASS1_MAX["height_m"] or
        length_m > CLASS1_MAX["length_m"]
    )

    if beyond_class1:
        permit_class = "special"
        permit_description = (
            "Special permit required — one or more dimensions exceed Class 1 maximums. "
            "Contact NHVR and the relevant state road authority for a special assessment "
            "before planning this route."
        )
    else:
        permit_class = "class1"
        permit_description = (
            "NHVR Class 1 permit required — vehicle dimensions exceed standard road limits. "
            "Apply via the NHVR Permit Portal before travel."
        )

    requires_pilot: list[str] = []
    requires_escort: list[str] = []
    state_flags: dict[str, list[str]] = {}

    overwidth  = width_m  > STANDARD_LIMITS["width_m"]
    overheight = height_m > STANDARD_LIMITS["height_m"]

    for state, rules in _STATE_RULES.items():
        flags: list[str] = []

        if overwidth:
            if width_m > rules["max_width_m"]:
                flags.append(
                    f"Width {width_m:.2f} m exceeds the {state} maximum of "
                    f"{rules['max_width_m']} m — travel requires special assessment."
                )
            elif width_m > rules["escort_width_m"]:
                flags.append(
                    f"Police/traffic controller escort required "
                    f"(width > {rules['escort_width_m']} m in {state})."
                )
                requires_escort.append(state)
            elif width_m > rules["pilot_width_m"]:
                flags.append(
                    f"Pilot vehicle required "
                    f"(width > {rules['pilot_width_m']} m in {state})."
                )
                requires_pilot.append(state)

        if overwidth or overheight:
            flags.append(rules["travel_note"])

        flags.extend(rules["extra"])
        state_flags[state] = flags

    return {
        "permit_class": permit_class,
        "permit_description": permit_description,
        "exceedances": exceedances,
        "requires_pilot": requires_pilot,
        "requires_escort": requires_escort,
        "state_flags": state_flags,
        "beyond_class1": beyond_class1,
    }
