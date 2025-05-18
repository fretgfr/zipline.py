from typing import Annotated, Optional

from aiohttp import NonHttpUrlClientError
from rich.progress import Progress, SpinnerColumn, TextColumn
from syncer import sync
from typer import Argument, Exit, Option, Typer

from zipline.client import Client
from zipline.errors import BadRequest, Forbidden, NotAuthenticated

app = Typer()


@app.command(name="shorten")
@sync
async def shorten(
    original_url: Annotated[
        str,
        Argument(help="The url you wish to shorten."),
    ],
    server_url: Annotated[
        str,
        Option(
            "--server",
            "-s",
            help="Specify the URL to your Zipline instance.",
            envvar="ZIPLINE_SERVER",
            prompt=True,
        ),
    ],
    token: Annotated[
        str,
        Option(
            "--token",
            "-t",
            help="Specify a token used for authentication against your chosen Zipline instance.",
            envvar="ZIPLINE_TOKEN",
            prompt=True,
            hide_input=True,
        ),
    ],
    vanity: Annotated[
        Optional[str],
        Option(
            "--vanity",
            "-v",
            help="Specify a vanity name. A name will be generated automatically if this is not provided.",
        ),
    ] = None,
    max_views: Annotated[
        Optional[int],
        Option(
            "--max-views",
            "-m",
            help="Specify the number of times this url can be used before being deleted. No limit will be set if this is not provided.",
        ),
    ] = None,
    password: Annotated[
        Optional[str],
        Option("--password", "-p", help="Specify a password required to use the url."),
    ] = None,
    enabled: Annotated[
        bool,
        Option(
            "--enable/--disable",
            "-e/-d",
            help="Specify whether the url should be immediately usable. If the url is disabled, you will need to use the Zipline website to enable it manually.",
        ),
    ] = True,
) -> None:
    """Upload a file to a remote Zipline instance."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Preparing client...", total=None)
        client = Client(server_url, token)

        progress.update(task, description="Creating shortened url...", total=None)
        try:
            shortened_url = await client.shorten_url(
                original_url=original_url,
                vanity=vanity,
                max_views=max_views,
                password=password,
                enabled=enabled,
            )
        except NonHttpUrlClientError as e:
            print(f"Invalid URL provided: '{server_url}'")
            await client.close()
            raise Exit(1) from e
        except (NotAuthenticated, Forbidden) as e:
            print("Authentication failure! Are you using a valid token?")
            await client.close()
            raise Exit(77) from e
        except BadRequest as e:
            print("Bad request!")
            await client.close()
            raise Exit(1) from e

        await client.close()

    print(shortened_url)
