import sys
import webbrowser

import click
import uvicorn

from stamped.core.config import settings


@click.group()
def cli() -> None:
    """Stamped — your outdoor photos on a conquest map."""


@cli.command()
@click.option("--port", default=None, type=int, help="Override default port.")
@click.option("--no-browser", is_flag=True, help="Do not open the browser automatically.")
def start(port: int | None, no_browser: bool) -> None:
    """Start the Stamped server and open the browser."""
    p = port or settings.port
    if not no_browser:
        webbrowser.open(f"http://localhost:{p}")
    uvicorn.run("stamped.api.main:app", host="127.0.0.1", port=p, reload=False)


@cli.command()
@click.argument("path")
def index(path: str) -> None:
    """Index a folder of photos and GPX tracks."""
    click.echo(f"Indexing {path} — not yet implemented.")


@cli.command()
def status() -> None:
    """Show system status."""
    import httpx

    try:
        r = httpx.get(f"http://localhost:{settings.port}/api/status", timeout=2)
        data = r.json()
        click.echo(f"Photos : {data['photos_total']}")
        click.echo(f"Thumbs : {data['thumbs_done']} done / {data['thumbs_pending']} pending")
        click.echo(f"Orphans: {data['orphans']}")
        click.echo(f"Quests : {data['quests']}")
        click.echo(f"GPX    : {data['gpx_files']}")
    except Exception:
        click.echo("Server is not running. Start with: stamped start", err=True)
        sys.exit(1)
