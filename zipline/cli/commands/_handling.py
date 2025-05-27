from typing import NoReturn

from aiohttp import NonHttpUrlClientError
from rich import print
from typer import Exit

from zipline.errors import BadRequest, Forbidden, NotAuthenticated, ServerError


def _maybe_raise_exit(exception: Exception, traceback: bool = False, code: int = 1) -> NoReturn:
    if traceback is True:
        raise exception
    raise Exit(code) from exception


def handle_api_errors(exception: Exception, server_url: str, traceback: bool = False) -> NoReturn:
    """
    Simple error handling to avoid huge tracebacks in the console when something errors.
    If something isn't caught by this function, the full traceback will be shown to help debugging.
    """

    error_string: str = f"[bold red]([yellow]{str(exception)}[red])"
    if isinstance(exception, NonHttpUrlClientError):
        print(f"[bold red]Invalid URL provided: '[bold yellow]{server_url}[bold red]'")
        _maybe_raise_exit(exception, traceback)
    if isinstance(exception, NotAuthenticated) or isinstance(exception, Forbidden):
        print(f"[bold red]Authentication failure! Are you using a valid token? {error_string}")
        _maybe_raise_exit(exception, traceback, code=77)
    if isinstance(exception, BadRequest):
        print(f"[bold red]Bad request! {error_string}")
        _maybe_raise_exit(exception, traceback)
    if isinstance(exception, ServerError):
        print(f"[bold red]Zipline encountered an internal server error! {error_string}")
        _maybe_raise_exit(exception, traceback)
    print(f"[bold red]Encountered a fatal error! {error_string}")
    _maybe_raise_exit(exception, traceback=True)  # always print traceback if the error encountered is unexpected
