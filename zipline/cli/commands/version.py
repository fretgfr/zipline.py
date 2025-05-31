from importlib.metadata import version
from typing import Dict, Optional

from rich import print
from typer import Typer

from zipline import meta

app = Typer()


def _get_package_version(package_name: str) -> Optional[str]:
    """Safely get package version with error handling."""
    try:
        return version(package_name)
    except ImportError:
        return None


@app.command(name="version")
def show_versions() -> None:
    """Shows versions of the zipline.py, aiohttp, typer, click, and rich packages."""
    versions: Dict[str, Optional[str]] = {
        meta.__title__: meta.__version__,
        "aiohttp": _get_package_version("aiohttp"),
        "typer": _get_package_version("typer"),
        "click": _get_package_version("click"),
        "rich": _get_package_version("rich"),
    }

    output = "\n".join(
        f"[blue]{name}:[/blue] {f'[bright_cyan]{version}[/bright_cyan]' if version else '[bold red]Not available[/bold red]'}"
        for name, version in versions.items()
    )

    print(output)
