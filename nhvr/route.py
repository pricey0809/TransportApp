"""
Maps NHVR Network API responses to a normalised RouteResult.

The NHVR Network API returns network *definitions* (which approved networks exist
for a vehicle type), not a point-to-point route approval verdict directly.

Confirmed response fields (from /network/networks):
  networkId, networkName, networkDisplayName, description, networkType,
  status ("Active"/"Inactive"), activationDate, retirementDate,
  fileReferences, createdAt, createdBy

The traffic-light approval status (green/orange/red) used on the NHVR Route
Planner map is in the Spatial API (still in development). Until that API is
available, this module infers approval status from network existence and
the network name/description where possible.
"""

from dataclasses import dataclass, field
from nhvr.vehicles import get_vehicle_label, VEHICLE_CODES  # noqa: F401 — VEHICLE_CODES kept for compat


@dataclass
class RouteResult:
    status: str                          # approved | conditional | restricted | unknown
    status_detail: str
    vehicle_label: str
    networks: list[dict] = field(default_factory=list)   # matching NHVR network records
    conditions: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)
    raw: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status":        self.status,
            "status_detail": self.status_detail,
            "vehicle_label": self.vehicle_label,
            "networks":      self.networks,
            "conditions":    self.conditions,
            "restrictions":  self.restrictions,
            "raw":           self.raw,
        }


def interpret_network_response(
    networks: list[dict],
    vehicle_code: str,
    origin: str,
    destination: str,
    vehicle_label: str = "",
) -> RouteResult:
    """
    Interpret a list of NHVR network records for a given vehicle type.

    Logic:
    - If active networks are found for the vehicle type → approved (or conditional
      if any network description mentions conditions).
    - If no active networks found → unknown (direct the user to the NHVR Route Planner
      for authoritative information).

    This will be upgraded to a precise traffic-light status once the NHVR
    Spatial API becomes available.
    """
    vehicle_label = vehicle_label or get_vehicle_label(vehicle_code)

    active = [n for n in networks if str(n.get("status", "")).lower() == "active"]

    if not networks:
        return RouteResult(
            status="unknown",
            status_detail=(
                f"No network records were returned for {vehicle_label}. "
                "Use the NHVR Route Planner for authoritative route information."
            ),
            vehicle_label=vehicle_label,
            raw=networks,
        )

    if not active:
        return RouteResult(
            status="unknown",
            status_detail=(
                f"Historical restrictions exist for this network but none are currently active. "
                f"Verify your specific route in the NHVR Route Planner before travel."
            ),
            vehicle_label=vehicle_label,
            networks=networks,
            raw=networks,
        )

    # Check descriptions for conditional keywords
    condition_keywords = ("condition", "permit", "approval", "restriction", "only", "except")
    conditions = []
    for n in active:
        desc = (n.get("description") or n.get("networkDisplayName") or "").lower()
        if any(kw in desc for kw in condition_keywords):
            conditions.append(
                n.get("networkDisplayName") or n.get("networkName") or n.get("networkId")
            )

    status = "conditional" if conditions else "approved"
    detail_map = {
        "approved": (
            f"{vehicle_label} has {len(active)} active network(s). "
            "Verify your specific route in the NHVR Route Planner."
        ),
        "conditional": (
            f"{vehicle_label} has active networks but some include conditions. "
            "Check the NHVR Route Planner for your exact route."
        ),
    }

    return RouteResult(
        status=status,
        status_detail=detail_map[status],
        vehicle_label=vehicle_label,
        networks=[_summarise_network(n) for n in active],
        conditions=conditions,
        raw=networks,
    )


def _summarise_network(n: dict) -> dict:
    """Return a display-friendly subset of a network record."""
    return {
        "id":          n.get("networkId"),
        "name":        n.get("networkDisplayName") or n.get("networkName"),
        "type":        n.get("networkType"),
        "description": n.get("description"),
        "active_from": n.get("activationDate"),
    }
