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

from __future__ import annotations

import datetime
import io
import mimetypes
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .http import HTTPClient, Route
from .utils import _guess_mime, parse_iso_timestamp, safe_get

__all__ = (
    "File",
    "User",
    "PartialInvite",
    "Invite",
    "Folder",
    "ShortenedURL",
    "UploadResponse",
    "FileData",
)


@dataclass
class File:
    """Represents a file stored on Zipline.

    Attributes
    ----------
    created_at: :class:`datetime.datetime`
        When the File was created.
    expires_at: Optional[:class:`datetime.datetime`]
        When the File expires.
    name: :class:`str`
        The name of the File.
    mimetype: :class:`str`
        The MIME type of the File.
    id: :class:`int`
        The id for the File.
    favorite: :class:`bool`
        Whether the File is favorited.
    views: :class:`int`
        The number of times the File has been viewed.
    folder_id: Optional[:class:`int`]
        The id of the Folder this File belongs to, None if the File is not in a Folder.
    max_views: Optional[:class:`int`]
        The number of times the File can be viewed before being removed. None if there is no limit.
    size: :class:`int`
        The size of the File in bytes.
    url: :class:`str`
        The url if the File. Note this does not contain the base url.
    original_name: Optional[:class:`str`]
        The original_name of the File. None if this information wasn't kept on upload.
    """

    __slots__ = (
        "http",
        "created_at",
        "expires_at",
        "name",
        "mimetype",
        "id",
        "favorite",
        "views",
        "folder_id",
        "max_views",
        "size",
        "url",
        "original_name",
    )

    http: HTTPClient
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime]
    name: str
    mimetype: str
    id: int
    favorite: bool
    views: int
    folder_id: Optional[int]
    max_views: Optional[int]
    size: int  # in bytes
    url: str
    original_name: Optional[str]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, http: HTTPClient) -> File:
        expires_at = data.get("expiresAt", None)
        expires_at_dt = parse_iso_timestamp(expires_at) if expires_at is not None else None
        fields = {
            "created_at": parse_iso_timestamp(data["createdAt"]),
            "expires_at": expires_at_dt,
            "name": data["name"],
            "mimetype": data["mimetype"],
            "id": data["id"],
            "favorite": data["favorite"],
            "views": data["views"],
            "folder_id": data["folderId"],
            "max_views": data["maxViews"],
            "size": data["size"],
            "url": data["url"],
            "original_name": data.get("originalName"),
        }
        return cls(http=http, **fields)

    async def read(self) -> bytes:
        """|coro|

        Read the File into memory.

        Returns
        -------
        bytes
            The data of the File
        """
        r = Route("GET", self.url)
        return await self.http.request(r)

    async def delete(self) -> None:
        """|coro|

        Delete this File.

        Raises
        ------
        NotFound
            The file could not be found.
        """
        data = {"id": self.id, "all": False}
        r = Route("DELETE", "/api/user/files")
        await self.http.request(r, json=data)

    async def edit(self, *, favorite: Optional[bool] = None) -> File:
        """|coro|

        Edit this File.

        Parameters
        ----------
        favorite: Optional[:class:`bool`]
            Whether this File is favorited., by default None

        Returns
        -------
        :class:`File`
            The edited File.

        Raises
        ------
        NotFound
            The File could not be found.
        """
        data = {"id": self.id, "favorite": favorite}
        r = Route("PATCH", "/api/user/files")
        js = await self.http.request(r, json=data)
        return File._from_data(js, http=self.http)

    @property
    def full_url(self) -> str:
        """Returns the full URL of this File."""
        return f"{self.http.base_url}{self.url}"


@dataclass
class User:
    """Represents a Zipline User.

    Attributes
    ----------
    id: :class:`int`
        The User's id.
    username: :class:`str`
        The User's username
    avatar: Optional[:class:`str`]
        The User's avatar, encoded in base64. None if they don't have one set.
    token: :class:`str`
        The User's token
    administrator: :class:`bool`
        Whether the User is an administrator
    super_admin: :class:`bool`
        Whether the User is a super admin
    system_theme: :class:`str`
        The User's preferred theme
    embed: Dict[:class:`str`, Any]
        The User's embed data, raw.
    ratelimit: Optional[:class:`int`]
        The User's ratelimit between File uploads, in seconds.
    totp_secret: Optional[:class:`str`]
        The User's Time-based One-Time Password (TOTP) secret. This secret is used for two-factor authentication (2FA).
        It is a unique secret key associated with the user's account. If set, the user can generate time-based one-time passwords
        using this secret to enhance the security of their account.
    domains: List[:class:`str`]
        List of domains the User has configured.
    """

    __slots__ = (
        "http",
        "id",
        "username",
        "avatar",
        "token",
        "administrator",
        "super_admin",
        "system_theme",
        "embed",
        "ratelimit",
        "totp_secret",
        "domains",
    )

    http: HTTPClient
    id: int
    username: str
    avatar: Optional[str]  # Base64 data
    token: str
    administrator: bool
    super_admin: bool
    system_theme: str
    embed: Dict[str, Any]
    ratelimit: Optional[int]
    totp_secret: Optional[str]
    domains: List[str]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, http: HTTPClient) -> User:
        fields = {
            "id": data["id"],
            "username": data["username"],
            "avatar": data["avatar"],
            "token": data["token"],
            "administrator": data["administrator"],
            "super_admin": data["superAdmin"],
            "system_theme": data["systemTheme"],
            "embed": data["embed"],
            "ratelimit": data["ratelimit"],
            "totp_secret": data["totpSecret"],
            "domains": data["domains"],
        }

        return cls(http=http, **fields)


@dataclass
class PartialInvite:
    """Represents a partial Zipline invite. This is returned by Client.create_invites.

    Attributes
    ----------
    code: :class:`str`
        The invite code generated.
    created_by_id: :class:`int`
        The id of the User that created this invite.
    expires_at: Optional[:class:`datetime.datetime`]
        When this invite expires. None if the invite does not expire.
    """

    __slots__ = ("code", "created_by_id", "expires_at")

    code: str
    created_by_id: int
    expires_at: Optional[datetime.datetime]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> PartialInvite:
        fields = {
            "code": data["code"],
            "created_by_id": data["createdById"],
            "expires_at": parse_iso_timestamp(data["expiresAt"]) if data.get("expiresAt") is not None else None,
        }

        return cls(**fields)


@dataclass
class Invite:
    """Represents a Zipline invite.

    Attributes
    ----------
    code: :class:`str`
        The Invite code.
    id: :class:`int`
        The Invite id.
    created_at: :class:`datetime.datetime`
        When the Invite was created.
    expires_at: Optional[:class:`datetime.datetime`]
        When the Invite expires. None if it does not expire.
    used: :class:`bool`
        Whether the Invite has been used.
    created_by_id: :class:`int`
        The id of the User that created this Invite.
    """

    __slots__ = (
        "http",
        "code",
        "id",
        "created_at",
        "expires_at",
        "used",
        "created_by_id",
    )

    http: HTTPClient
    code: str
    id: int
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime]
    used: bool
    created_by_id: int

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, http: HTTPClient) -> Invite:
        fields = {
            "id": data["id"],
            "code": data["code"],
            "created_at": data["createdAt"],
            "expires_at": data.get("expiresAt"),
            "used": data["used"],
            "created_by_id": data["createdById"],
        }

        return cls(http=http, **fields)

    @property
    def url(self):
        """The full url of this invite."""
        return f"{self.http.base_url}/auth/register?code={self.code}"

    async def delete(self) -> Invite:
        """|coro|

        Delete this Invite.

        Returns
        -------
        :class:`Invite`
            The deleted Invite.

        Raises
        ------
        NotFound
            The Invite could not be found
        """
        query_params = {"code": self.code}
        r = Route("DELETE", "/api/auth/invite")
        js = await self.http.request(r, params=query_params)
        return Invite._from_data(js, http=self.http)


@dataclass
class Folder:
    """Represents a Zipline folder.

    Attributes
    ----------
    id: :class:`int`
        The id of the Folder
    name: :class:`str`
        The name of the Folder
    user_id: :class:`int`
        The id of the User that owns the Folder.
    created_at: :class:`datetime.datetime`
        When the Folder was created.
    updated_at: :class:`datetime.datetime`
        When the folder was last updated.
    files: List[:class:`~zipline.models.File`]
        The Files in this Folder, if any. None if the Folder was fetched without files.
    public: :class:`bool`
        Whether this folder is public.

        .. versionadded:: 0.16.0
    """

    # TODO FOLDER SPECIFIC ACTIONS FROM "/api/user/folders/[id]" should be implemented here

    __slots__ = (
        "http",
        "id",
        "name",
        "user_id",
        "created_at",
        "updated_at",
        "files",
        "public",
    )

    http: HTTPClient
    id: int
    name: str
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    files: List[File] | None
    public: bool

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, http: HTTPClient) -> Folder:
        files = data.get("files")
        fields = {
            "id": data["id"],
            "name": data["name"],
            "user_id": data["userId"],
            "created_at": parse_iso_timestamp(data["createdAt"]),
            "updated_at": parse_iso_timestamp(data["updatedAt"]),
            "files": [File._from_data(f, http=http) for f in files] if files is not None else None,
            "public": data["public"],
        }

        return cls(http=http, **fields)

    async def add_file(self, file: File, /) -> None:
        """|coro|

        Adds a File to this Folder

        Parameters
        ----------
        file: :class:`File`
            The File to add.

        Raises
        ------
        BadRequest
            There was an error adding the file
        UnhandledError
            An unexpected exception occured, please report this to the developer.
        """
        data = {
            "file": file.id,
        }
        r = Route("POST", f"/api/user/folders/{self.id}")
        await self.http.request(r, json=data)

    async def remove_file(self, file: File, /):
        """|coro|

        Removes a File from this Folder

        Parameters
        ----------
        file: :class:`File`
            The File to remove.

        Raises
        ------
        BadRequest
            There was an error removing the file
        UnhandledError
            An unexpected exception occured, please report this to the developer.
        """
        data = {
            "file": file.id,
        }

        r = Route("DELETE", f"/api/user/folders/{self.id}")
        await self.http.request(r, json=data)

    @property
    async def url(self) -> str:
        return f"{self.http.base_url}/folder/{self.id}"


@dataclass
class ShortenedURL:
    """Represents a shortened url on Zipline.

    Attributes
    ----------
    created_at: :class:`datetime.datetime`
        When the url was created.
    id: :class:`int`
        The id of the url.
    destination: :class:`str`
        The destination url.
    vanity: Optional[:class:`str`]
        The vanity url of this invite. None if this isn't a vanity url.
    views: :class:`int`
        The number of times this invite has been used.
    max_views: Optional[:class:`int`]
        The number of times this url can be viewed before deletion. None if there is no limit.
    url: :class:`str`
        The url path to use this. Note this does not include the base url.
    """

    __slots__ = (
        "http",
        "created_at",
        "id",
        "destination",
        "vanity",
        "views",
        "max_views",
        "url",
    )

    http: HTTPClient
    created_at: datetime.datetime
    id: int
    destination: str
    vanity: Optional[str]
    views: int
    max_views: Optional[int]
    url: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, http: HTTPClient) -> ShortenedURL:
        fields = {
            "created_at": parse_iso_timestamp(data["createdAt"]),
            "id": data["id"],
            "destination": data["destination"],
            "vanity": data.get("vanity"),
            "views": data["views"],
            "max_views": data.get("maxViews"),
            "url": data["url"],
        }

        return cls(http=http, **fields)

    @property
    def full_url(self) -> str:
        return f"{self.http.base_url}{self.url}"

    async def delete(self) -> None:
        """|coro|

        Deletes this :class:`ShortenedURL`.
        """
        data = {"id": self.id}
        r = Route("DELETE", "/api/user/urls")
        await self.http.request(r, json=data)


@dataclass
class UploadResponse:
    """Represents a response to a File upload.

    Attributes
    ----------
    file_urls: List[:class:`str`]
        The urls of the Files that were uploaded.
    expires_at: Optional[:class:`datetime.datetime`]
        When the uploads expire. None if they do not expire.
    removed_gps: Optional[:class:`bool`]
        Whether gps data was removed from the uploads.
    """

    __slots__ = ("file_urls", "expires_at", "removed_gps")

    file_urls: List[str]
    expires_at: Optional[datetime.datetime]
    removed_gps: Optional[bool]

    @classmethod
    def _from_data(cls, data: Dict[str, Any]) -> UploadResponse:
        expires_at = data.get("expiresAt")
        fields = {
            "file_urls": data["files"],
            "expires_at": parse_iso_timestamp(expires_at) if expires_at is not None else None,
            "removed_gps": data.get("removed_gps"),
        }

        return cls(**fields)


class FileData:
    """Used to upload a File to Zipline.

    Attributes
    ----------
    data: Union[:class:`str`, :class:`bytes`, :class:`os.PathLike`, :class:`io.BufferedIOBase`]
        The file or file like object to open.
    filename: Optional[:class:`str`]
        The name of the file to be uploaded. Defaults to filename of the given path, if applicable.
    mimetype: Optional[:class:`str`]
        The MIME type of the file, if None the lib will attemp to determine it.
    """

    __slots__ = ("filename", "data", "mimetype")

    def __init__(
        self,
        data: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase],
        filename: Optional[str] = None,
        *,
        mimetype: Optional[str] = None,
    ) -> None:
        """Used to upload a file to Zipline.

        Parameters
        ----------
        data: Union[:class:`str`, :class:`bytes`, :class:`os.PathLike`, :class:`io.BufferedIOBase`]
            The file or file like object to open.
        filename: Optional[:class:`str`]
            The name of the file to be uploaded. Defaults to filename of the given path, if applicable.
        mimetype: Optional[:class:`str`]
            The MIME type of the file, if None the lib will attempt to determine it.

        Raises
        ------
        ValueError
            An invalid value was passed to the data parameter.
        TypeError
            The MIME type of the file could not be determined and was not provided.
        """
        if isinstance(data, io.IOBase):
            if not (data.seekable() and data.readable()):
                raise ValueError(f"File buffer {data!r} must be seekable and readable")
            self.data: io.BufferedIOBase = data
        else:
            self.data = open(data, "rb")

        # Mime type determination. Strategy is:
        #   - an explicitly given type
        #   - a guessed type based on the filename, if present.
        #   - a guessed type based on magic bytes
        #   - application/octet-stream as a fallback.
        if mimetype is not None:
            guessed_mime = mimetype
        elif filename is not None:
            guessed_mime = mimetypes.guess_type(filename)[0]
        elif filename is None and mimetype is None:
            guessed_mime = _guess_mime(self.data.read(16))
            # back it up again
            self.data.seek(0)

        self.mimetype = guessed_mime or "application/octet-stream"

        if filename is None:
            if isinstance(data, str):
                _, filename = os.path.split(data)
            else:
                filename = getattr(data, "name", "untitled")

        self.filename = filename

        if self.mimetype is None:
            raise TypeError("could not determine mimetype of file given")


@dataclass
class ServerVersionInfo:
    """Information about the current Zipline version.

    Attributes
    ----------
    is_upstream: :class:`bool`
        Whether the version being run is current.
    update_to_type: :class:`str`
        The branch being tracked.
    stable_version: :class:`str`
        The current stable version of Zipline.
    upstream_version: :class:`str`
        The current GitHub version of Zipline.
    current_version: :class:`str`
        The version of Zipline installed on this server.
    """

    __slots__ = (
        "is_upstream",
        "update_to_type",
        "stable_version",
        "upstream_version",
        "current_version",
    )

    is_upstream: bool
    update_to_type: str
    stable_version: str
    upstream_version: str
    current_version: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> ServerVersionInfo:
        is_upstream = data.get("isUpstream")
        update_to_type = data.get("updateToType")
        stable_version = safe_get(data, "versions", "stable")
        upstream_version = safe_get(data, "versions", "upstream")
        current_version = safe_get(data, "versions", "current")

        return cls(is_upstream, update_to_type, stable_version, upstream_version, current_version)  # type: ignore
