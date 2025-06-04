from asyncio import run
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

from typing_extensions import ParamSpec

Params = ParamSpec("Params")
Response = TypeVar("Response")


def sync(
    func: Callable[Params, Coroutine[Any, Any, Response]],
) -> Callable[Params, Response]:
    """
    Decorator that takes an async function `func(...) -> Coroutine[Any, Any, Response]`
    and turns it into a synchronous function `() -> Response` by running
    `asyncio.run(...)` under the hood.
    """

    @wraps(wrapped=func)
    def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Response:
        return run(func(*args, **kwargs))

    return wrapper
