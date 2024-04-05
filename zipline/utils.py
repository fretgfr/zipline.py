"""
Copyright 2023-present fretgfr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import datetime
from itertools import islice
from operator import attrgetter
from typing import Any, AsyncIterable, Coroutine, Dict, Generator, Iterable, Optional, Tuple, TypeVar, Union, overload

__all__ = (
    "as_chunks",
    "get",
    "utcnow",
)

T = TypeVar("T")
_Iter = Union[Iterable[T], AsyncIterable[T]]
Coro = Coroutine[Any, Any, T]


def parse_iso_timestamp(iso_str: str, /) -> datetime.datetime:
    """Parses an iso string to an aware UTC datetime."""
    return datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)


def to_iso_format(dt: datetime.datetime, /) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def utcnow() -> datetime.datetime:
    """Returns an aware UTC datetime representing the current time.

    Returns
    --------
    :class:`datetime.datetime`
        The current aware datetime in UTC.
    """
    return datetime.datetime.now(datetime.timezone.utc)


# From the python docs for 3.12s `itertools.batched`
def as_chunks(iterable: Iterable[T], n: int) -> Generator[Tuple[T, ...], None, None]:
    """Batches an iterable into chunks of up to size n.

    Parameters
    ----------
    iterable : :class:`collections.abc.Iterable`
        The iterable to batch
    n : :class:`int`
        The number of elements per generated tuple.

    Raises
    ------
    :class:`ValueError`
        At least one result must be returned per group.
    """
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


# The following get utility was sourced from discord.py under the MIT license.
def _get(iterable: Iterable[T], /, **attrs: Any) -> Optional[T]:
    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace("__", "."))
        return next((elem for elem in iterable if pred(elem) == v), None)

    converted = [(attrget(attr.replace("__", ".")), value) for attr, value in attrs.items()]
    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


async def _aget(iterable: AsyncIterable[T], /, **attrs: Any) -> Optional[T]:
    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace("__", "."))
        async for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [(attrget(attr.replace("__", ".")), value) for attr, value in attrs.items()]

    async for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


@overload
def get(iterable: AsyncIterable[T], /, **attrs: Any) -> Coro[Optional[T]]: ...


@overload
def get(iterable: Iterable[T], /, **attrs: Any) -> Optional[T]: ...


def get(iterable: _Iter[T], /, **attrs: Any) -> Union[Optional[T], Coro[Optional[T]]]:
    r"""A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``.

    When multiple attributes are specified, they are checked using
    logical AND, not logical OR. Meaning they have to meet every
    attribute passed in and not one of them.

    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x__y`` as the keyword argument.

    If nothing is found that matches the attributes passed, then
    ``None`` is returned.


    Parameters
    -----------
    iterable: Union[:class:`collections.abc.Iterable`, :class:`collections.abc.AsyncIterable`]
        The iterable to search through. Using a :class:`collections.abc.AsyncIterable`,
        makes this function return a coroutine.
    \*\*attrs
        Keyword arguments that denote attributes to search with.
    """

    return (
        _aget(iterable, **attrs)  # type: ignore
        if hasattr(iterable, "__aiter__")  # isinstance(iterable, collections.abc.AsyncIterable) is too slow
        else _get(iterable, **attrs)  # type: ignore
    )


def safe_get(dict_: Dict[Any, Any], *keys: Any) -> Optional[Any]:
    """Safely get a nested key from a dictionary.

    ex.
    .. code-block:: python3

        d = {
            'i': 1,
            'j': {
                'k': '2'
            }
        }

        safe_get(d, 'i')  # -> 1
        safe_get(d, 'j', 'k')  # -> '2'


    Parameters
    ----------
    dict_ : Dict[Any, Any]
        The dictionary to get the key from
    keys : Any
        The keys to get from the dictionary. Processed in order.

    Returns
    -------
    Optional[Any]
        The value at the key. None if the key could not be gotten.
    """
    for key in keys:
        try:
            dict_ = dict_[key]
        except KeyError:
            return None

    return dict_


def _guess_mime(data: bytes) -> Optional[str]:
    """
    Sourced: https://en.wikipedia.org/wiki/List_of_file_signatures

    Handled types:
        - jpeg
        - png
        - webp
        - gif
        - mp4
        - mkv
        - mp3
        - mov
    """
    if data[0:3] == b"\xff\xd8\xff" or data[6:10] in (b"JFIF", b"Exif"):
        return "image/jpeg"
    elif data.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
        return "image/png"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    elif data.startswith((b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61")):
        return "image/gif"
    elif data[3:11] in (b"\x66\x74\x79\x70\x4d\x53\x4e\x56", b"\x66\x74\x79\x70\x69\x73\x6f\x6d"):
        return "video/mp4"
    elif data[0:4] == b"\x1a\x45\xdf\xa3":
        return "video/x-matroska"
    elif data[0:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") or data[0:3] == b"\x49\x44\x43":
        return "audio/mpeg"
    elif data[0:4] == b"\x6d\x6f\x6f\x76":
        return "video/quicktime"
    else:
        return None
