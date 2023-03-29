__all__ = ("ZiplineError", "UnhandledError", "BadRequest", "Forbidden", "NotFound", "ServerError", "NotAuthenticated")


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
    """Server returned a 401 response."""

    pass


class NotFound(ZiplineError):
    """Server returned a 404 response."""


class ServerError(ZiplineError):
    """Server returned a 500 response code."""

    pass


class NotAuthenticated(ZiplineError):
    """Requesting data without an Authorization header"""

    pass
