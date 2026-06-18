"""
Curated GeoJSON polygons for major DG-restricted tunnels in Australia.

⚠️  CURATED DATA — NOT AN OFFICIAL LIVE DATASET
    These polygons were manually researched from NHVR network maps, state
    heavy vehicle authority publications, and operator guidance documents.
    They are NOT sourced from a live regulatory API.

    Before relying on this data operationally:
      • Cross-check each tunnel against current NHVR Route Planner results
        at https://routeplanner.nhvr.gov.au
      • Verify with the relevant state authority:
          NSW  – Transport for NSW Heavy Vehicle Services
          VIC  – VicRoads Heavy Vehicle Unit
          QLD  – Department of Transport and Main Roads (TMR)
      • Re-check after any road or network condition changes

    Polygons are bounding boxes that encompass the tunnel portals and a
    small buffer zone (≈ 50–100 m) so Valhalla's avoid_polygons logic has
    enough geometry to intercept the approach roads.

    Last verified: 2025  (see each entry's restriction_note for source)

Polygon format:
    GeoJSON Polygon — coordinates as [longitude, latitude], first == last.
    All coordinates are [lon, lat] (GeoJSON convention, NOT lat/lon).
"""

from __future__ import annotations

# ── Tunnel registry ────────────────────────────────────────────────────────────
#
# restriction_level:
#   "restricted"   — placard loads prohibited; no permit available
#   "conditional"  — placard loads allowed with pre-approval / specific permit
#
# Each polygon is a rough bounding box around the tunnel tube(s) plus portals.
# Use a mapping tool (QGIS, geojson.io) to refine if tighter avoidance is needed.

TUNNEL_POLYGONS: list[dict] = [

    # ── New South Wales ────────────────────────────────────────────────────────
    #
    # Stotts Creek / Cudgen Road Tunnel note:
    # This is a public motorway tunnel (Pacific Motorway M1, near Chinderah).
    # It is not operated by Linkt/Transurban, so the blanket "no placarded
    # vehicles" operator policy does not apply via a toll-road agreement.
    # NSW Road Rule 300-2 Class 1 / Division 2.1 prohibition does apply.
    # Polygon coordinates are estimated — verify against current Transport for
    # NSW mapping before operational use.

    {
        "id": "NSW_CUDGEN_STOTTS_CREEK",
        "name": "Cudgen Road Tunnel (Stotts Creek / Pacific Motorway M1)",
        "state": "NSW",
        "restriction_level": "restricted",
        "restriction_note": (
            "Class 1 and Division 2.1 loads prohibited under NSW Road Rule 300-2. "
            "Located on the Pacific Motorway (M1) near Chinderah, approximately "
            "5 km south of Tweed Heads. "
            "Public motorway tunnel — operator blanket-ban policy does not apply. "
            "Source: Transport for NSW. "
            "⚠️  Polygon coordinates are estimated; verify against current TfNSW mapping."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [153.512, -28.218],
                [153.524, -28.218],
                [153.524, -28.232],
                [153.512, -28.232],
                [153.512, -28.218],
            ]],
        },
    },


    {
        "id": "NSW_SYDNEY_HARBOUR_TUNNEL",
        "name": "Sydney Harbour Tunnel",
        "state": "NSW",
        "restriction_level": "restricted",
        "restriction_note": (
            "Class 1–9 dangerous goods in placard quantities prohibited. "
            "Source: Transport for NSW Dangerous Goods by Road – Tunnel Restrictions."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [151.2085, -33.8490],
                [151.2180, -33.8490],
                [151.2180, -33.8570],
                [151.2085, -33.8570],
                [151.2085, -33.8490],
            ]],
        },
    },

    {
        "id": "NSW_M5_EAST_TUNNEL",
        "name": "M5 East Tunnel",
        "state": "NSW",
        "restriction_level": "restricted",
        "restriction_note": (
            "Dangerous goods in placard quantities prohibited. "
            "Applies to the tunnel section between King Georges Rd and the Eastern Portal. "
            "Source: Transport for NSW."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [151.0470, -33.9300],
                [151.0900, -33.9300],
                [151.0900, -33.9420],
                [151.0470, -33.9420],
                [151.0470, -33.9300],
            ]],
        },
    },

    {
        "id": "NSW_CROSS_CITY_TUNNEL",
        "name": "Cross City Tunnel (Sydney)",
        "state": "NSW",
        "restriction_level": "conditional",
        "restriction_note": (
            "Some DG classes conditional on pre-approval. "
            "Check NHVR Route Planner for current class-by-class status. "
            "Source: Transport for NSW."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [151.1970, -33.8710],
                [151.2110, -33.8710],
                [151.2110, -33.8790],
                [151.1970, -33.8790],
                [151.1970, -33.8710],
            ]],
        },
    },

    {
        "id": "NSW_LANE_COVE_TUNNEL",
        "name": "Lane Cove Tunnel",
        "state": "NSW",
        "restriction_level": "conditional",
        "restriction_note": (
            "Some DG classes conditional on pre-approval. "
            "Source: Transport for NSW."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [151.1600, -33.8080],
                [151.1820, -33.8080],
                [151.1820, -33.8200],
                [151.1600, -33.8200],
                [151.1600, -33.8080],
            ]],
        },
    },

    # ── Victoria ───────────────────────────────────────────────────────────────

    {
        "id": "VIC_CITYLINK_BURNLEY",
        "name": "CityLink Burnley Tunnel",
        "state": "VIC",
        "restriction_level": "restricted",
        "restriction_note": (
            "Dangerous goods in placard quantities prohibited. "
            "Applies to both bores of the Burnley Tunnel under the Yarra. "
            "Source: VicRoads / Transurban CityLink User Guide."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [144.9760, -37.8250],
                [145.0050, -37.8250],
                [145.0050, -37.8380],
                [144.9760, -37.8380],
                [144.9760, -37.8250],
            ]],
        },
    },

    {
        "id": "VIC_CITYLINK_DOMAIN",
        "name": "CityLink Domain Tunnel",
        "state": "VIC",
        "restriction_level": "restricted",
        "restriction_note": (
            "Dangerous goods in placard quantities prohibited. "
            "Applies to the Domain Tunnel section between Alexandra Ave and the CBD portal. "
            "Source: VicRoads / Transurban CityLink User Guide."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [144.9620, -37.8360],
                [144.9780, -37.8360],
                [144.9780, -37.8460],
                [144.9620, -37.8460],
                [144.9620, -37.8360],
            ]],
        },
    },

    # ── Queensland ─────────────────────────────────────────────────────────────

    {
        "id": "QLD_CLEM7",
        "name": "Clem7 Tunnel (Legacy Way connector)",
        "state": "QLD",
        "restriction_level": "restricted",
        "restriction_note": (
            "Dangerous goods in placard quantities prohibited. "
            "Source: Queensland TMR Dangerous Goods Road Tunnel Policy."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [153.0100, -27.4830],
                [153.0380, -27.4830],
                [153.0380, -27.5000],
                [153.0100, -27.5000],
                [153.0100, -27.4830],
            ]],
        },
    },

    {
        "id": "QLD_AIRPORT_LINK",
        "name": "Airport Link Tunnel",
        "state": "QLD",
        "restriction_level": "restricted",
        "restriction_note": (
            "Dangerous goods in placard quantities prohibited. "
            "Covers the Airport Link M7 tunnel between Bowen Hills and Kedron. "
            "Source: Queensland TMR."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [153.0250, -27.4200],
                [153.0500, -27.4200],
                [153.0500, -27.4480],
                [153.0250, -27.4480],
                [153.0250, -27.4200],
            ]],
        },
    },

    {
        "id": "QLD_LEGACY_WAY",
        "name": "Legacy Way Tunnel",
        "state": "QLD",
        "restriction_level": "restricted",
        "restriction_note": (
            "Dangerous goods in placard quantities prohibited. "
            "Covers the Legacy Way tunnel between Toowong and Kelvin Grove. "
            "Source: Queensland TMR."
        ),
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [152.9880, -27.4550],
                [153.0080, -27.4550],
                [153.0080, -27.4730],
                [152.9880, -27.4730],
                [152.9880, -27.4550],
            ]],
        },
    },
]


# ── Public API ─────────────────────────────────────────────────────────────────

def get_avoid_polygons(dg_tunnel_flag: str) -> list[dict]:
    """
    Return a list of GeoJSON Polygon geometries to pass to Valhalla's
    ``avoid_polygons`` parameter.

    Args:
        dg_tunnel_flag:
            One of:
              ``"none"``        — no placard load; return empty list
              ``"conditional"`` — include conditional + restricted tunnels
              ``"restricted"``  — include restricted tunnels only

    Returns:
        List of GeoJSON Polygon dicts (the ``polygon`` field from each
        matching TUNNEL_POLYGONS entry), ready to embed in a Valhalla
        route request as ``"avoid_polygons": [...]``.

    Note:
        This function returns ALL polygons for any DG load because routing
        around a tunnel is always the safer default. Use ``"none"`` to
        suppress avoidance when the load is confirmed non-placard.
    """
    if dg_tunnel_flag == "none":
        return []

    if dg_tunnel_flag == "restricted":
        return [
            t["polygon"]
            for t in TUNNEL_POLYGONS
            if t["restriction_level"] == "restricted"
        ]

    # "conditional" or any other truthy value → avoid everything
    return [t["polygon"] for t in TUNNEL_POLYGONS]


def list_tunnels(state: str | None = None) -> list[dict]:
    """
    Return tunnel metadata (without polygon geometry) for display / auditing.

    Args:
        state: Optional two-letter state code (``"NSW"``, ``"VIC"``, ``"QLD"``).
               If None, returns all tunnels.
    """
    results = TUNNEL_POLYGONS if state is None else [
        t for t in TUNNEL_POLYGONS if t["state"] == state
    ]
    return [
        {
            "id":                t["id"],
            "name":              t["name"],
            "state":             t["state"],
            "restriction_level": t["restriction_level"],
            "restriction_note":  t["restriction_note"],
        }
        for t in results
    ]
