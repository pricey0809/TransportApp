"""
Australian Dangerous Goods (ADG) Code — placard load classification.

Thresholds are from the ADG Code 7th Edition, Table 5.3 (placard load quantities).
Tunnel categories align with ADG Code Chapter 8 / ADR provisions.
Segregation requirements are derived from ADG Code Table 7.5.

Always verify against the current edition of the ADG Code and relevant state
road authority requirements before travel.

Reference: https://www.ntc.gov.au/codes-and-guidelines/australian-dangerous-goods-code
"""

# ── DG Class / Division list ───────────────────────────────────────────────────

DG_CLASSES = [
    {"code": "1.1",  "label": "1.1 — Mass explosion hazard"},
    {"code": "1.2",  "label": "1.2 — Projection hazard"},
    {"code": "1.3",  "label": "1.3 — Fire / minor blast / minor projection hazard"},
    {"code": "1.4",  "label": "1.4 — No significant hazard"},
    {"code": "1.4S", "label": "1.4S — Compatibility Group S (minor hazard)"},
    {"code": "1.5",  "label": "1.5 — Very insensitive, mass explosion hazard"},
    {"code": "1.6",  "label": "1.6 — Extremely insensitive articles"},
    {"code": "2.1",  "label": "2.1 — Flammable gases (excl. aerosols)"},
    {"code": "2.2",  "label": "2.2 — Non-flammable, non-toxic gases"},
    {"code": "2.3",  "label": "2.3 — Toxic gases"},
    {"code": "3",    "label": "3 — Flammable liquids"},
    {"code": "4.1",  "label": "4.1 — Flammable solids"},
    {"code": "4.2",  "label": "4.2 — Spontaneously combustible substances"},
    {"code": "4.3",  "label": "4.3 — Substances dangerous when wet"},
    {"code": "5.1",  "label": "5.1 — Oxidising substances"},
    {"code": "5.2",  "label": "5.2 — Organic peroxides"},
    {"code": "6.1",  "label": "6.1 — Toxic substances"},
    {"code": "6.2",  "label": "6.2 — Infectious substances"},
    {"code": "7",    "label": "7 — Radioactive material"},
    {"code": "8",    "label": "8 — Corrosive substances"},
    {"code": "9",    "label": "9 — Miscellaneous dangerous goods"},
]

# Classes requiring packing group input (threshold varies by PG)
PG_CLASSES = {"3", "5.1"}

# ── Placard load thresholds — ADG Code 7th Edition, Table 5.3 ─────────────────
#
# "always"                   — placard load at any quantity
# "threshold"                — aggregate quantity in the stated unit
# "packing_group_thresholds" — {PG: threshold} where PG changes the value
# "unit"                     — "L" (litres / water capacity for gases) or "kg"
# "note"                     — human-readable threshold summary

_THRESHOLDS: dict = {
    # Class 1 — Explosives: always a placard load
    # (Transport governed by the Australian Code for the Transport of
    # Explosives by Road and Rail, 3rd edition)
    "1.1":  {"always": True,  "unit": None,
             "note": "Any quantity of Class 1 explosives constitutes a placard load."},
    "1.2":  {"always": True,  "unit": None,
             "note": "Any quantity of Class 1 explosives constitutes a placard load."},
    "1.3":  {"always": True,  "unit": None,
             "note": "Any quantity of Class 1 explosives constitutes a placard load."},
    "1.4":  {"always": True,  "unit": None,
             "note": "Any quantity of Class 1 explosives constitutes a placard load."},
    "1.4S": {"always": True,  "unit": None,
             "note": "Any quantity of Class 1.4S constitutes a placard load."},
    "1.5":  {"always": True,  "unit": None,
             "note": "Any quantity of Class 1 explosives constitutes a placard load."},
    "1.6":  {"always": True,  "unit": None,
             "note": "Any quantity of Class 1.6 constitutes a placard load."},

    # Class 2 — Gases
    # Quantity measured as aggregate water capacity in litres
    "2.1":  {"always": False, "threshold": 250,  "unit": "L",
             "note": "Flammable gases: 250 L aggregate water capacity (lower threshold)."},
    "2.2":  {"always": False, "threshold": 1000, "unit": "L",
             "note": "Non-flammable, non-toxic gases: 1,000 L aggregate water capacity."},
    "2.3":  {"always": False, "threshold": 250,  "unit": "L",
             "note": "Toxic gases: 250 L aggregate water capacity (lower threshold)."},

    # Class 3 — Flammable liquids (threshold by packing group)
    "3":    {"always": False, "unit": "L",
             "packing_group_thresholds": {"I": 50, "II": 250, "III": 1000},
             "note": "PG I: 50 L  |  PG II: 250 L  |  PG III: 1,000 L"},

    # Class 4
    "4.1":  {"always": False, "threshold": 1000, "unit": "kg",
             "note": "Flammable solids: 1,000 kg aggregate. PG I substances may have a lower threshold — verify."},
    "4.2":  {"always": False, "threshold": 1000, "unit": "kg",
             "note": "Spontaneously combustible: 1,000 kg aggregate."},
    "4.3":  {"always": False, "threshold": 1000, "unit": "kg",
             "note": "Dangerous when wet: 1,000 kg aggregate. PG I substances may have a lower threshold — verify."},

    # Class 5
    "5.1":  {"always": False, "unit": "kg",
             "packing_group_thresholds": {"I": 50, "II": 250, "III": 1000},
             "note": "PG I: 50 kg  |  PG II: 250 kg  |  PG III: 1,000 kg"},
    "5.2":  {"always": False, "threshold": 1000, "unit": "kg",
             "note": "Organic peroxides: 1,000 kg aggregate."},

    # Class 6
    "6.1":  {"always": False, "threshold": 1000, "unit": "kg",
             "note": "Toxic substances: 1,000 kg aggregate. PG I substances may trigger lower 250 kg threshold — verify."},
    "6.2":  {"always": False, "threshold": 10,   "unit": "kg",
             "note": "Non-Category A: 10 kg. Category A (UN 2814/UN 2900): always a placard load."},

    # Class 7 — Radioactive
    # Governed by ARPANSA Code of Practice for the Safe Transport of
    # Radioactive Substances. Cannot compute from quantity alone.
    "7":    {"always": False, "threshold": None, "unit": None,
             "note": "Yellow III label: always a placard load. White I / Yellow II: consult ARPANSA."},

    # Class 8
    "8":    {"always": False, "threshold": 1000, "unit": "kg",
             "note": "Corrosive substances: 1,000 kg aggregate. PG I substances may have a lower threshold — verify."},

    # Class 9
    "9":    {"always": False, "threshold": 1000, "unit": "kg",
             "note": "Miscellaneous dangerous goods: 1,000 kg aggregate."},
}

# ── Tunnel restriction flags ───────────────────────────────────────────────────
#
# ⚠️  LEGISLATIVE VS. OPERATOR POLICY CONFLICT — READ BEFORE MODIFYING
#
# Two distinct sources govern DG access to Australian road tunnels, and they
# do NOT agree:
#
# 1. NSW Road Rule 300-2 (strict legislative wording)
#    Prohibits vehicles carrying goods if the load:
#      (a) includes Class 1 (explosives, any division), OR
#      (b) includes Division 2.1 (flammable gas), OR
#      (c) requires more than one placard OR a mixed-class placard.
#    A single-class placard load outside Class 1 / Division 2.1 is NOT
#    automatically prohibited by this rule.  Other Australian states may have
#    equivalent road rules with slightly different wording — this flag
#    implementation uses NSW Road Rule 300-2 as the primary legislative
#    reference.
#
# 2. Toll road operator policy (Linkt / Transurban published guidance)
#    States broadly "no placarded dangerous goods vehicles" without class
#    distinction.  This is enforced as a condition of the tunnel user
#    agreement and applies at CityLink (VIC), M5 East, Cross City, Lane Cove,
#    Airport Link, Legacy Way, and Clem7 regardless of DG class.
#
# The flags below use "restricted" ONLY where NSW Road Rule 300-2 explicitly
# names the class.  All other placard loads are "conditional" because the
# operator's blanket ban applies even though the rule does not.
#
# THIS INTERPRETATION HAS NOT BEEN CONFIRMED AGAINST CURRENT NHVR OR EPA
# GUIDANCE AND MUST NOT BE RELIED UPON OPERATIONALLY WITHOUT VERIFICATION.
# Getting this wrong has real compliance consequences.  The "conditional" flag
# is the conservative default for any class not explicitly named in the rule.
#
# The mixed-class trigger (condition (c) above) CANNOT be detected from a
# single DG class input.  Operators carrying multiple DG classes must treat
# the load as caught by NSW Road Rule 300-2 regardless of which classes are
# present individually.
#
# "none" | "conditional" | "restricted"
#   none        — no tunnel restriction flagged under any current source
#   conditional — NOT prohibited by NSW Road Rule 300-2 for a single-class
#                 placard load, but tunnel operator policy may prohibit it;
#                 confirm with the operator and relevant road authority
#   restricted  — explicitly prohibited under NSW Road Rule 300-2 (Class 1 or
#                 Division 2.1) or equivalent state road rule

_TUNNEL_FLAGS: dict[str, tuple[str, str | None]] = {

    # ── Class 1 — Explosives ───────────────────────────────────────────────────
    # Explicitly named in NSW Road Rule 300-2 as a prohibited class.
    # Basis: legislative (Road Rule 300-2 and equivalent state rules).

    "1.1":  ("restricted",
             "Class 1.1 (mass explosion hazard) is explicitly prohibited from "
             "road tunnels under NSW Road Rule 300-2 and equivalent state rules. "
             "This is a legislative prohibition — not solely operator policy. "
             "Pre-approval from the relevant state road authority is required."),
    "1.2":  ("restricted",
             "Class 1.2 (projection hazard) is explicitly prohibited from "
             "road tunnels under NSW Road Rule 300-2 and equivalent state rules. "
             "Pre-approval required."),
    "1.3":  ("restricted",
             "Class 1.3 (fire/blast hazard) is explicitly prohibited from "
             "road tunnels under NSW Road Rule 300-2 and equivalent state rules. "
             "Pre-approval required."),
    "1.4":  ("restricted",
             "Class 1.4 (minor hazard) is part of Class 1 (explosives), which is "
             "explicitly prohibited under NSW Road Rule 300-2. "
             "Although Class 1.4 is lower-hazard than other Class 1 divisions, "
             "the rule does not exempt it by division. "
             "Confirm with the road authority before travel."),
    "1.4S": ("conditional",
             "Class 1.4S (Compatibility Group S, Consumer Fireworks) is not "
             "explicitly identified as a separate category in NSW Road Rule 300-2. "
             "It is part of Class 1 and may be subject to the same tunnel "
             "prohibition; many operators apply a blanket ban. "
             "Confirm with the relevant road authority before travel."),
    "1.5":  ("restricted",
             "Class 1.5 (very insensitive, mass explosion hazard) is part of "
             "Class 1 and is explicitly prohibited under NSW Road Rule 300-2. "
             "Pre-approval required."),
    "1.6":  ("restricted",
             "Class 1.6 (extremely insensitive articles) is part of Class 1 and "
             "falls under the NSW Road Rule 300-2 prohibition. "
             "Confirm with the road authority given the lower net explosive content."),

    # ── Division 2.1 — Flammable gas ──────────────────────────────────────────
    # Explicitly named in NSW Road Rule 300-2 as a prohibited class.
    # Basis: legislative (Road Rule 300-2 and equivalent state rules).

    "2.1":  ("restricted",
             "Division 2.1 (flammable gas) is explicitly named in NSW Road Rule "
             "300-2 as a prohibited class in road tunnels. "
             "This is a legislative prohibition, not solely operator policy. "
             "Confirm with the relevant state road authority and tunnel operator."),

    # ── Division 2.2 — Non-flammable, non-toxic gas ────────────────────────────
    # Not named in NSW Road Rule 300-2 for a single-class load.
    # Operator policy: some operators apply a blanket ban — verify.

    "2.2":  ("none",
             "Division 2.2 (non-flammable, non-toxic gas) is not explicitly "
             "prohibited by NSW Road Rule 300-2 for a single-class placard load. "
             "However, some tunnel operators (Linkt/Transurban) apply a blanket "
             "'no placarded vehicles' policy regardless of class. "
             "Confirm with the tunnel operator before travel."),

    # ── Division 2.3 — Toxic gas ───────────────────────────────────────────────
    # NOT named as a specific trigger in NSW Road Rule 300-2 (only Class 1 and
    # Division 2.1 are explicitly named). A single-class Class 2.3 placard load
    # is NOT automatically prohibited under the strict legislative wording.
    # However, operator policy and the inherent hazard make confirmation
    # essential.  Flagged conditional rather than restricted.
    #
    # ⚠️  This may conflict with how operators actually enforce the policy —
    # confirm before travel.

    "2.3":  ("conditional",
             "Division 2.3 (toxic gas) is NOT explicitly named in NSW Road Rule "
             "300-2 as a prohibited class for a single-class placard load. "
             "Under the strict legislative wording, the rule only applies to "
             "Class 1 and Division 2.1 (and to mixed/multi-placard loads). "
             "However, tunnel operators (Linkt/Transurban) apply a blanket "
             "'no placarded vehicles' policy that would cover Class 2.3. "
             "⚠️  This interpretation has not been confirmed against current "
             "NHVR or EPA guidance. Treat as prohibited until verified with "
             "the operator and relevant road authority."),

    # ── Class 3 — Flammable liquids ────────────────────────────────────────────
    # NOT named as a specific trigger in NSW Road Rule 300-2 for a single-class
    # placard load. Operator policy applies.

    "3":    ("conditional",
             "Class 3 (flammable liquids) is NOT explicitly named in NSW Road "
             "Rule 300-2 as a prohibited class for a single-class placard load. "
             "Under the strict legislative wording, the rule applies to Class 1 "
             "and Division 2.1 only (and to mixed/multi-placard loads). "
             "Tunnel operators (Linkt/Transurban) apply a blanket "
             "'no placarded vehicles' policy that would cover Class 3. "
             "⚠️  This interpretation conflicts with how operators publicly "
             "describe the policy. Confirm with the operator and road authority."),

    # ── Class 4 ────────────────────────────────────────────────────────────────

    "4.1":  ("none",
             "Class 4.1 (flammable solids) is not specifically flagged for "
             "tunnel restrictions in NSW Road Rule 300-2 for a single-class "
             "placard load. However, some operators apply a blanket "
             "'no placarded vehicles' policy — confirm before travel."),
    "4.2":  ("conditional",
             "Class 4.2 (spontaneously combustible substances) is NOT explicitly "
             "named in NSW Road Rule 300-2 for a single-class placard load. "
             "Operator policy (Linkt/Transurban blanket ban on placarded vehicles) "
             "may apply. Confirm with the tunnel operator and road authority."),
    "4.3":  ("conditional",
             "Class 4.3 (dangerous when wet) is NOT explicitly named in NSW Road "
             "Rule 300-2 for a single-class placard load. "
             "Operator policy (blanket ban) may apply. Confirm before travel."),

    # ── Class 5 ────────────────────────────────────────────────────────────────

    "5.1":  ("conditional",
             "Class 5.1 (oxidising substances) is NOT explicitly named in NSW "
             "Road Rule 300-2 for a single-class placard load. "
             "Operator policy (Linkt/Transurban blanket ban) may apply. "
             "Confirm with the tunnel operator and road authority."),
    "5.2":  ("conditional",
             "Class 5.2 (organic peroxides) is NOT explicitly named in NSW Road "
             "Rule 300-2 for a single-class placard load. "
             "Operator policy may apply. Confirm before travel."),

    # ── Class 6 ────────────────────────────────────────────────────────────────

    "6.1":  ("conditional",
             "Class 6.1 (toxic substances) is NOT explicitly named in NSW Road "
             "Rule 300-2 for a single-class placard load. "
             "Operator policy (blanket ban) may apply. Confirm before travel."),
    "6.2":  ("conditional",
             "Class 6.2 (infectious substances) is NOT explicitly named in NSW "
             "Road Rule 300-2 for a single-class placard load as an automatic "
             "tunnel prohibition. "
             "Operator policy and state health/emergency requirements may apply. "
             "Consult state health authorities, the tunnel operator, and the road "
             "authority before travel."),

    # ── Class 7 — Radioactive ──────────────────────────────────────────────────

    "7":    ("conditional",
             "Class 7 (radioactive material) is NOT explicitly named in NSW Road "
             "Rule 300-2 for a single-class placard load, but restrictions depend "
             "on label category, activity level, and your radiation transport plan. "
             "Radioactive Yellow III loads are generally treated as prohibited from "
             "tunnels by most operators. "
             "Consult ARPANSA, the tunnel operator, and relevant road authority."),

    # ── Class 8 — Corrosives ───────────────────────────────────────────────────
    # Not named in NSW Road Rule 300-2 for a single-class placard load.

    "8":    ("none",
             "Class 8 (corrosive substances) is not specifically prohibited by "
             "NSW Road Rule 300-2 for a single-class placard load. "
             "Some operators apply a blanket 'no placarded vehicles' policy — "
             "confirm with the tunnel operator before travel."),

    # ── Class 9 — Miscellaneous ────────────────────────────────────────────────

    "9":    ("none",
             "Class 9 (miscellaneous dangerous goods) is not specifically "
             "prohibited by NSW Road Rule 300-2 for a single-class placard load. "
             "Some operators apply a blanket 'no placarded vehicles' policy — "
             "confirm with the tunnel operator before travel."),
}

# ── Segregation requirements — simplified from ADG Code Table 7.5 ─────────────
# Classes that MUST NOT be carried together with the key class.

_SEGREGATION: dict[str, list[str]] = {
    "1.1":  ["2.1", "3", "4.1", "4.2", "4.3", "5.1", "5.2", "6.1", "8"],
    "1.2":  ["2.1", "3", "4.1", "4.2", "4.3", "5.1", "5.2", "6.1", "8"],
    "1.3":  ["2.1", "3", "4.1", "4.2", "5.1", "5.2"],
    "1.4":  ["5.1"],
    "1.4S": [],
    "1.5":  ["2.1", "3", "4.1", "4.2", "4.3", "5.1", "5.2", "6.1", "8"],
    "1.6":  [],
    "2.1":  ["1.1", "1.2", "1.3", "1.5", "3"],
    "2.2":  [],
    "2.3":  ["1.1", "1.2", "1.3", "1.5"],
    "3":    ["1.1", "1.2", "1.3", "1.5", "2.1", "5.1"],
    "4.1":  ["1.1", "1.2", "1.3", "1.5", "5.1", "5.2"],
    "4.2":  ["1.1", "1.2", "1.3", "1.5", "5.1", "5.2"],
    "4.3":  ["1.1", "1.2", "1.3", "1.5", "8"],
    "5.1":  ["1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "3", "4.1", "4.2"],
    "5.2":  ["1.1", "1.2", "1.3", "1.5", "4.1", "4.2"],
    "6.1":  ["1.1", "1.2", "1.3", "1.5"],
    "6.2":  [],   # "all other classes" handled as special case below
    "7":    [],   # activity-level dependent — flagged via warnings
    "8":    ["1.1", "1.2", "1.3", "1.5", "4.3"],
    "9":    [],
}

_VALID_CLASSES = {d["code"] for d in DG_CLASSES}


def classify_dg_load(
    dg_class: str,
    un_number: str,
    quantity: float,
    packing_group: str | None = None,
) -> dict:
    """
    Determine whether a dangerous goods load is a placard load under the ADG Code
    and flag tunnel restrictions and segregation requirements.

    Args:
        dg_class:      DG class/division code (e.g. "2.1", "3", "6.2")
        un_number:     UN number as a 4-digit string (e.g. "1203"), may be empty
        quantity:      Aggregate quantity in kg or litres
        packing_group: "I", "II", or "III" — required for Class 3 and 5.1

    Returns dict:
        is_placard_load     — bool (None for Class 7 — indeterminate)
        placard_description — human-readable summary
        dg_class_label      — full label string for the class
        threshold_note      — threshold rule in effect
        tunnel_flag         — "none" | "conditional" | "restricted"
        tunnel_note         — explanation string or None
        segregation_classes — list of class codes incompatible with this load
        warnings            — list of additional advisory strings
        un_number           — echoed back
        dg_class            — echoed back
        quantity            — echoed back
        packing_group       — effective packing group used
    """
    if dg_class not in _VALID_CLASSES:
        return {"error": f"Unknown DG class: {dg_class!r}"}

    thresh = _THRESHOLDS[dg_class]
    dg_label = next(d["label"] for d in DG_CLASSES if d["code"] == dg_class)

    warnings: list[str] = []
    is_placard: bool | None = False
    placard_description = ""
    effective_pg = packing_group

    # ── Determine placard load status ─────────────────────────────────────────

    if thresh["always"]:
        is_placard = True
        placard_description = (
            f"Class {dg_class} explosives are always a placard load regardless of quantity. "
            "Approved dangerous goods driver licence, placards, emergency information panel (EIP), "
            "and emergency information documentation are required."
        )
        warnings.append(
            "Transport of Class 1 explosives is also governed by the Australian Code for the "
            "Transport of Explosives by Road and Rail (3rd edition). Additional permit and "
            "notification requirements apply."
        )

    elif dg_class == "6.2":
        warnings.append(
            "If this is a Category A infectious substance (UN 2814 or UN 2900), it is always "
            "a placard load regardless of quantity."
        )
        if quantity >= thresh["threshold"]:
            is_placard = True
            placard_description = (
                f"Quantity {quantity} kg meets or exceeds the {thresh['threshold']} kg "
                "placard threshold for Class 6.2 (non-Category A). This is a placard load."
            )
        else:
            is_placard = False
            placard_description = (
                f"Quantity {quantity} kg is below the {thresh['threshold']} kg placard "
                "threshold for Class 6.2 (non-Category A). Not a placard load unless Category A."
            )

    elif dg_class == "7":
        is_placard = None  # Indeterminate — depends on label category
        placard_description = (
            "Placard requirement for Class 7 depends on the radioactive label category. "
            "Radioactive Yellow III: always a placard load. "
            "White I and Yellow II: may be exempt. "
            "Consult ARPANSA and your radiation transport plan."
        )
        warnings.append(
            "Class 7 transport is regulated by the ARPANSA Code of Practice for the Safe "
            "Transport of Radioactive Substances. A radiation transport plan is required."
        )

    elif "packing_group_thresholds" in thresh:
        pg = (packing_group or "").upper().replace("PG", "").replace(" ", "")
        pg_thresholds = thresh["packing_group_thresholds"]

        if pg not in pg_thresholds:
            pg = "I"
            effective_pg = "I"
            warnings.append(
                f"Packing group not specified for Class {dg_class}. "
                "Using PG I (most restrictive threshold) as a conservative estimate."
            )
        else:
            effective_pg = pg

        threshold = pg_thresholds[pg]
        unit = thresh["unit"]

        if quantity >= threshold:
            is_placard = True
            placard_description = (
                f"Quantity {quantity} {unit} meets or exceeds the placard threshold of "
                f"{threshold} {unit} for Class {dg_class} Packing Group {pg}. "
                "This is a placard load."
            )
        else:
            is_placard = False
            placard_description = (
                f"Quantity {quantity} {unit} is below the placard threshold of "
                f"{threshold} {unit} for Class {dg_class} Packing Group {pg}. "
                "Not a placard load at this quantity."
            )
        warnings.append(
            "Any single receptacle with a capacity exceeding 500 L or 500 kg "
            "constitutes a placard load regardless of aggregate quantity "
            "(ADG Code clause 5.3)."
        )

    else:
        threshold = thresh["threshold"]
        unit = thresh["unit"]

        if quantity >= threshold:
            is_placard = True
            placard_description = (
                f"Quantity {quantity} {unit} meets or exceeds the placard threshold of "
                f"{threshold:,} {unit} for Class {dg_class}. This is a placard load."
            )
        else:
            is_placard = False
            placard_description = (
                f"Quantity {quantity} {unit} is below the placard threshold of "
                f"{threshold:,} {unit} for Class {dg_class}. Not a placard load at this quantity."
            )
        warnings.append(
            "Any single receptacle with a capacity exceeding 500 L or 500 kg "
            "constitutes a placard load regardless of aggregate quantity "
            "(ADG Code clause 5.3)."
        )

    # ── Tunnel flags ──────────────────────────────────────────────────────────
    #
    # tunnel_flag values:
    #   "restricted"  — explicitly prohibited by NSW Road Rule 300-2
    #                   (Class 1 any division, Division 2.1)
    #   "conditional" — NOT caught by NSW Road Rule 300-2 for this single class,
    #                   but tunnel operator policy (Linkt/Transurban blanket ban)
    #                   may apply; confirm before travel
    #   "none"        — not flagged under any current source for a single-class
    #                   placard load; operator policy may still apply

    tunnel_flag, tunnel_note = _TUNNEL_FLAGS.get(dg_class, ("none", None))

    # Classes explicitly covered by NSW Road Rule 300-2
    _NSW_RULE_300_2_CLASSES = frozenset({"1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "2.1"})

    # tunnel_policy_conflict: True when the tunnel_flag was derived from operator
    # policy rather than the strict legislative text of NSW Road Rule 300-2.
    # False for "restricted" (legislative basis) and for "none" with no operator
    # policy concern.  Always True for "conditional" — the exact threshold between
    # "operator bans it" and "legislation bans it" is unresolved.
    tunnel_policy_conflict: bool = (
        tunnel_flag == "conditional"
        or (tunnel_flag == "none" and is_placard is True and dg_class not in _NSW_RULE_300_2_CLASSES)
    )

    # For any placard load, warn about the mixed-class trigger in NSW Road Rule 300-2.
    # A load carrying two or more DG classes, or requiring a mixed-class placard,
    # triggers the rule even if each individual class is not explicitly listed.
    if is_placard is True and tunnel_flag != "restricted":
        warnings.append(
            "Mixed-class / multi-placard warning: NSW Road Rule 300-2 also "
            "prohibits tunnel access for loads that require more than one placard "
            "OR a mixed-class placard, regardless of the individual class. "
            "If this vehicle carries multiple DG classes or has mixed placards, "
            "the tunnel prohibition applies even though the single-class flag for "
            f"Class {dg_class} is '{tunnel_flag}' here."
        )

    if tunnel_policy_conflict and is_placard is True:
        warnings.append(
            "⚠️  POLICY CONFLICT — tunnel restriction basis: "
            "NSW Road Rule 300-2 (strict legislative wording) does NOT explicitly "
            f"prohibit Class {dg_class} single-class placard loads from road tunnels. "
            "However, toll road operators (Linkt, Transurban) publicly state "
            "'no placarded dangerous goods vehicles' without class distinction. "
            "This conflict has not been resolved by current NHVR or EPA published "
            "guidance. Do NOT rely on this flag operationally without verification "
            "against the current NHVR Route Planner and the relevant tunnel operator."
        )

    # ── Segregation ───────────────────────────────────────────────────────────
    seg = _SEGREGATION.get(dg_class, [])
    segregation_note: str | None = None

    if dg_class == "6.2":
        segregation_classes = ["all other classes"]
        segregation_note = (
            "Class 6.2 (Category A) infectious substances must be segregated from "
            "all other dangerous goods."
        )
    elif dg_class == "7":
        segregation_classes = []
        segregation_note = (
            "Segregation requirements for Class 7 depend on the activity level and label "
            "category. Consult ARPANSA and your radiation transport plan."
        )
    else:
        segregation_classes = seg

    return {
        "is_placard_load":       is_placard,
        "placard_description":   placard_description,
        "dg_class":              dg_class,
        "dg_class_label":        dg_label,
        "threshold_note":        thresh.get("note", ""),
        "tunnel_flag":           tunnel_flag,
        "tunnel_note":           tunnel_note,
        "tunnel_policy_conflict": tunnel_policy_conflict,
        "segregation_classes":   segregation_classes,
        "segregation_note":      segregation_note,
        "warnings":              warnings,
        "un_number":             un_number,
        "quantity":              quantity,
        "packing_group":         effective_pg,
    }
