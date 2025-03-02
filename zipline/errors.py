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

__all__ = (
    "ZiplineError",
    "UnhandledError",
    "BadRequest",
    "Forbidden",
    "NotFound",
    "RateLimited",
    "ServerError",
    "NotAuthenticated",
)


class ZiplineError(Exception):
    """Base class for Zipline related errors."""

    pass


class UnhandledError(ZiplineError):
    """Raised by the library if the server returns a status code not handled by the lib."""

    pass


class BadRequest(ZiplineError):
    """Server returned a 400 response."""

    pass


class Forbidden(ZiplineError):
    """Server returned a 401 or 403 response."""

    pass


class NotFound(ZiplineError):
    """Server returned a 404 response."""

    pass


class RateLimited(ZiplineError):
    """Server returned a 429 response."""

    pass


class ServerError(ZiplineError):
    """Server returned a 5xx response code."""

    pass


class NotAuthenticated(ZiplineError):
    """Requesting data without an Authorization header"""

    pass
