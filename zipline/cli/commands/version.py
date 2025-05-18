from importlib.metadata import version as get_version
from typing import Optional

import aiohttp
import click
import typer

from zipline import meta

app = typer.Typer()


def _get_package_version(package_name: str) -> Optional[str]:
    """Safely get package version with error handling."""
    try:
        return get_version(package_name)
    except ImportError:
        return None


@app.command(name="version")
def show_versions() -> None:
    """
    Display versions of key dependencies.

    Shows versions of the zipline.py, aiohttp, typer, click, and rich packages.
    """
    versions = {
        meta.__title__: meta.__version__,
        "aiohttp": aiohttp.__version__,
        "typer": typer.__version__,
        "click": click.__version__,
        "rich": _get_package_version("rich"),
    }

    output = "\n".join(
        f"{name}: {ver if ver else 'Not available'}" for name, ver in versions.items()
    )

    typer.echo(output)
