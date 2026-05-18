import logging

import httpx

logger = logging.getLogger(__name__)

_OPENTOPODATA_URL = "https://api.opentopodata.org/v1/mapzen"
_BATCH_SIZE = 100
_TIMEOUT = 30.0


def fetch_elevation(points: list[tuple[float, float]]) -> list[float | None]:
    """
    Fetch altitude for a list of (lat, lon) points via OpenTopoData (Mapzen model).

    Splits into batches of 100 (API limit). Returns None for each point whose
    altitude could not be retrieved (network error, API error, null result).
    Pure — no DB access, no side effects beyond the outbound HTTP call.
    """
    if not points:
        return []

    results: list[float | None] = []

    for batch_start in range(0, len(points), _BATCH_SIZE):
        batch = points[batch_start : batch_start + _BATCH_SIZE]
        locations = "|".join(f"{lat},{lon}" for lat, lon in batch)

        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                response = client.post(_OPENTOPODATA_URL, json={"locations": locations})
                response.raise_for_status()
                data = response.json()

            for entry in data["results"]:
                elevation = entry.get("elevation")
                results.append(float(elevation) if elevation is not None else None)

        except Exception:
            logger.warning(
                "Elevation fetch failed for batch [%d:%d]",
                batch_start,
                batch_start + len(batch),
                exc_info=True,
            )
            results.extend([None] * len(batch))

    return results
