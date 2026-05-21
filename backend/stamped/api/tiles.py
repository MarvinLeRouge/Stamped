import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, Response

from stamped.core.fs import get_tiles_dir

router = APIRouter()

_LAYERS: dict[str, dict[str, str]] = {
    "osm": {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "content_type": "image/png",
    },
    "topo": {
        "url": "https://tile.opentopomap.org/{z}/{x}/{y}.png",
        "content_type": "image/png",
    },
    "satellite": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "content_type": "image/jpeg",
    },
}

_HEADERS = {"User-Agent": "Stamped/0.1 (local personal use; https://github.com)"}


@router.get("/tiles/{z}/{x}/{y}.png")
async def get_tile_legacy(z: int, x: int, y: int) -> Response:
    return RedirectResponse(url=f"/api/tiles/osm/{z}/{x}/{y}")


@router.get("/tiles/{layer}/{z}/{x}/{y}")
async def get_tile(layer: str, z: int, x: int, y: int) -> Response:
    if layer not in _LAYERS:
        raise HTTPException(status_code=404, detail=f"Unknown layer: {layer}")

    cfg = _LAYERS[layer]
    ext = "jpg" if cfg["content_type"] == "image/jpeg" else "png"
    tile_path = get_tiles_dir() / layer / str(z) / str(x) / f"{y}.{ext}"

    if tile_path.exists():
        return Response(content=tile_path.read_bytes(), media_type=cfg["content_type"])

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                cfg["url"].format(z=z, x=x, y=y),
                headers=_HEADERS,
                timeout=10,
            )
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Tile fetch failed") from exc

    tile_path.parent.mkdir(parents=True, exist_ok=True)
    tile_path.write_bytes(r.content)

    return Response(content=r.content, media_type=cfg["content_type"])
