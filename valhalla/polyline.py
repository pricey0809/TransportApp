"""
Valhalla encoded polyline decoder.

Valhalla uses a 6-decimal-precision variant of the Google Encoded Polyline
Algorithm Format. The ``shape`` strings returned in ``trip.legs[*].shape``
must be decoded with precision=6 (Google Maps uses 5 — they are NOT interchangeable).

Output coordinates are in GeoJSON order: [longitude, latitude].
"""


def decode_shape(encoded: str, precision: int = 6) -> list[list[float]]:
    """
    Decode a Valhalla encoded polyline string to a list of [lon, lat] pairs.

    Args:
        encoded:   The ``shape`` string from a Valhalla route response leg.
        precision: Decimal precision. Valhalla uses 6; Google Maps uses 5.

    Returns:
        List of ``[longitude, latitude]`` pairs in GeoJSON coordinate order.

    Example::

        coords = decode_shape(trip["legs"][0]["shape"])
        geojson_line = {"type": "LineString", "coordinates": coords}
    """
    multiplier = 10 ** precision
    result: list[list[float]] = []
    index = lat = lng = 0

    while index < len(encoded):
        # Decode latitude delta
        shift = val = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            val |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += ~(val >> 1) if (val & 1) else (val >> 1)

        # Decode longitude delta
        shift = val = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            val |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lng += ~(val >> 1) if (val & 1) else (val >> 1)

        # GeoJSON is [longitude, latitude]
        result.append([lng / multiplier, lat / multiplier])

    return result
