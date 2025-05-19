from asyncio import run
from functools import wraps


def sync(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return run(func(*args, **kwargs))

    return wrapper
