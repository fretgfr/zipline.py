from asyncio import run
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

Response = TypeVar("Response")


def sync(
    func: Callable[..., Coroutine[Any, Any, Response]],
) -> Callable[..., Response]:
    """
    Decorator that takes an async function `func(...) -> Coroutine[Any, Any, Response]`
    and turns it into a synchronous function `() -> Response` by running
    `asyncio.run(...)` under the hood.
    """

    @wraps(wrapped=func)
    def wrapper(*args: Any, **kwargs: Any) -> Response:
        return run(func(*args, **kwargs))

    return wrapper
