from typing import NoReturn

from aiohttp import NonHttpUrlClientError
from rich import print
from typer import Exit

from zipline.errors import BadRequest, Forbidden, NotAuthenticated, ServerError


def handle_api_errors(error: Exception, server_url: str) -> NoReturn:
    """
    Simple error handling to avoid huge tracebacks in the console when something errors.
    If something isn't caught by this function, the full traceback will be shown to help debugging.
    """

    error_string: str = f"[bold red]([yellow]{str(error)}[red])"
    if isinstance(error, NonHttpUrlClientError):
        print(f"[bold red]Invalid URL provided: '[bold yellow]{server_url}[bold red]'")
        raise Exit(code=1) from error
    if isinstance(error, NotAuthenticated) or isinstance(error, Forbidden):
        print(f"[bold red]Authentication failure! Are you using a valid token? {error_string}")
        raise Exit(code=77) from error
    if isinstance(error, BadRequest):
        print(f"[bold red]Bad request! {error_string}")
        raise Exit(code=1) from error
    if isinstance(error, ServerError):
        print(f"[bold red]Zipline encountered an internal server error! {error_string}")
        raise Exit(code=1) from error
    print(f"[bold red]Encountered a fatal error: {error}")
    raise error
