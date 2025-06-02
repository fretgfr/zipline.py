import sys
from typing import Optional

from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Argument, Option, Typer

from zipline.cli.commands._handling import handle_api_errors
from zipline.cli.sync import sync
from zipline.client import Client

app = Typer()


@app.command(name="shorten")
@sync
async def shorten(
    original_url: str = Argument(help="The url you wish to shorten."),
    server_url: str = Option(
        ...,
        "--server",
        "-s",
        help="Specify the URL to your Zipline instance.",
        envvar="ZIPLINE_SERVER",
        prompt=True,
    ),
    token: str = Option(
        ...,
        "--token",
        "-t",
        help="Specify a token used for authentication against your chosen Zipline instance.",
        envvar="ZIPLINE_TOKEN",
        prompt=True,
        hide_input=True,
    ),
    print_object: bool = Option(
        bool(sys.stdout.isatty()),
        "--object/--text",
        "-o/-O",
        help=(
            "Choose how to format the output. If --text (or piped),\n"
            "you'll get the shortened url; if --object (or on a TTY),\n"
            "you'll get the raw Python object."
        ),
    ),
    vanity: Optional[str] = Option(
        None,
        "--vanity",
        "-v",
        help="Specify a vanity name. A name will be generated automatically if this is not provided.",
    ),
    max_views: Optional[int] = Option(
        None,
        "--max-views",
        "-m",
        help="Specify the number of times this url can be used before being deleted. No limit will be set if this is not provided.",
    ),
    password: Optional[str] = Option(None, "--password", "-p", help="Specify a password required to use the url."),
    enabled: bool = Option(
        True,
        "--enable/--disable",
        "-e/-d",
        help="Specify whether the url should be immediately usable. If the url is disabled, you will need to use the Zipline website to enable it manually.",
    ),
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Specify whether or not the application should print tracebacks from exceptions to the console. If the application encounters an exception it doesn't expect, it will always be printed to the console regardless of this option.",
        envvar="ZIPLINE_VERBOSE",
    ),
) -> None:
    """Shorten a url using a remote Zipline instance."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Creating shortened url...", total=None)
        async with Client(server_url, token) as client:
            try:
                shortened_url = await client.shorten_url(
                    original_url=original_url,
                    vanity=vanity,
                    max_views=max_views,
                    password=password,
                    enabled=enabled,
                )
            except Exception as exception:
                handle_api_errors(exception, server_url, traceback=verbose)

    print(shortened_url if print_object else str(shortened_url))
