import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from stamped.core.fs import get_tiles_dir

router = APIRouter()

_OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
_HEADERS = {"User-Agent": "Stamped/0.1 (local personal use; https://github.com)"}


@router.get("/tiles/{z}/{x}/{y}.png")
async def get_tile(z: int, x: int, y: int) -> Response:
    tile_path = get_tiles_dir() / str(z) / str(x) / f"{y}.png"

    if tile_path.exists():
        return Response(content=tile_path.read_bytes(), media_type="image/png")

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                _OSM_URL.format(z=z, x=x, y=y),
                headers=_HEADERS,
                timeout=10,
            )
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="OSM tile fetch failed") from exc

    tile_path.parent.mkdir(parents=True, exist_ok=True)
    tile_path.write_bytes(r.content)

    return Response(content=r.content, media_type="image/png")
