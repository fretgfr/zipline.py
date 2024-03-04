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

import io
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp

from .errors import BadRequest, NotFound, UnhandledError

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


@dataclass(slots=True)
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

    _session: aiohttp.ClientSession
    created_at: datetime
    expires_at: Optional[datetime]
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
    def _from_data(cls, data: Dict[str, Any], /, session: aiohttp.ClientSession) -> File:
        expires_at = data.get("expiresAt", None)
        expires_at_dt = datetime.fromisoformat(expires_at) if expires_at is not None else None
        fields = {
            "created_at": datetime.fromisoformat(data["createdAt"]),
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
        return cls(_session=session, **fields)

    async def read(self) -> bytes:
        """|coro|

        Read the File into memory.

        Returns
        -------
        bytes
            The data of the File
        """
        async with self._session.get(self.full_url) as resp:
            return await resp.read()

    async def delete(self) -> None:
        """|coro|

        Delete this File.

        Raises
        ------
        NotFound
            The file could not be found.
        """
        data = {"id": self.id, "all": False}
        async with self._session.delete("/api/user/files", json=data) as resp:
            status = resp.status
            if status == 200:
                return
            elif status == 404:
                raise NotFound("404: The file could not be found.")

        raise UnhandledError(f"Code {status} unhandled in File.delete!")

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
        async with self._session.patch("/api/user/files", json=data) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return File._from_data(js, session=self._session)
            elif status == 404:
                raise NotFound("404: File could not be found.")

        raise UnhandledError(f"Code {status} unhandled in File.delete!")

    @property
    def full_url(self) -> str:
        """Returns the full URL of this File."""
        return f"{self._session._base_url}{self.url}"


@dataclass(slots=True)
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

    _session: aiohttp.ClientSession
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
    def _from_data(cls, data: Dict[str, Any], /, session: aiohttp.ClientSession) -> User:
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

        return cls(_session=session, **fields)


@dataclass(slots=True)
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

    code: str
    created_by_id: int
    expires_at: Optional[datetime]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> PartialInvite:
        fields = {
            "code": data["code"],
            "created_by_id": data["createdById"],
            "expires_at": datetime.fromisoformat(data["expiresAt"]) if data.get("expiresAt") is not None else None,
        }

        return cls(**fields)


@dataclass(slots=True)
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

    _session: aiohttp.ClientSession
    code: str
    id: int
    created_at: datetime
    expires_at: Optional[datetime]
    used: bool
    created_by_id: int

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, session: aiohttp.ClientSession) -> Invite:
        fields = {
            "id": data["id"],
            "code": data["code"],
            "created_at": data["createdAt"],
            "expires_at": data.get("expiresAt"),
            "used": data["used"],
            "created_by_id": data["createdById"],
        }

        return cls(_session=session, **fields)

    @property
    def url(self):
        """The full url of this invite."""
        return f"{self._session._base_url}/auth/register?code={self.code}"

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

        async with self._session.delete("/api/auth/invite", params=query_params) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return Invite._from_data(js, session=self._session)
            elif status == 404:
                raise NotFound("404: Invite not found.")

        raise UnhandledError(f"Code {status} unhandled in Invite.delete!")


@dataclass(slots=True)
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
    _session: aiohttp.ClientSession
    id: int
    name: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    files: List[File] | None
    public: bool

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, session: aiohttp.ClientSession) -> Folder:
        files = data.get("files")
        fields = {
            "id": data["id"],
            "name": data["name"],
            "user_id": data["userId"],
            "created_at": datetime.fromisoformat(data["createdAt"]),
            "updated_at": datetime.fromisoformat(data["updatedAt"]),
            "files": [File._from_data(f, session=session) for f in files] if files is not None else None,
            "public": data["public"],
        }

        return cls(_session=session, **fields)

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
        async with self._session.post(f"/api/user/folders/{self.id}", json=data) as resp:
            status = resp.status

            if status == 200:
                return
            elif status == 400:
                msgjson = await resp.json()
                msg = msgjson["error"]
                raise BadRequest(f"400: {msg}")

        raise UnhandledError(f"Code {status} unhandled in add_file!")

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

        async with self._session.delete(f"/api/user/folders/{self.id}", json=data) as resp:
            status = resp.status

            if status == 200:
                return
            elif status == 400:
                msgjson = await resp.json()
                msg = msgjson["error"]
                raise BadRequest(f"400: {msg}")

        raise UnhandledError(f"Code {status} unhandled in remove_file!")

    @property
    async def url(self) -> str:
        return f"{self._session._base_url}/folder/{self.id}"


@dataclass(slots=True)
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

    _session: aiohttp.ClientSession
    created_at: datetime
    id: int
    destination: str
    vanity: Optional[str]
    views: int
    max_views: Optional[int]
    url: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, session: aiohttp.ClientSession) -> ShortenedURL:
        fields = {
            "created_at": datetime.fromisoformat(data["createdAt"]),
            "id": data["id"],
            "destination": data["destination"],
            "vanity": data.get("vanity"),
            "views": data["views"],
            "max_views": data.get("maxViews"),
            "url": data["url"],
        }

        return cls(_session=session, **fields)

    @property
    def full_url(self) -> str:
        return f"{self._session._base_url}{self.url}"

    async def delete(self) -> None:
        """|coro|

        Deletes this :class:`ShortenedURL`.
        """
        data = {"id": self.id}
        async with self._session.delete("/api/user/urls", json=data) as resp:
            status = resp.status
            if status == 200:
                return

        raise UnhandledError(f"Code {status} unhandled in ShortenedURL.delete!")


@dataclass(slots=True)
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

    file_urls: List[str]
    expires_at: Optional[datetime]
    removed_gps: Optional[bool]

    @classmethod
    def _from_data(cls, data: Dict[str, Any]) -> UploadResponse:
        expires_at = data.get("expiresAt")
        fields = {
            "file_urls": data["files"],
            "expires_at": datetime.fromisoformat(expires_at) if expires_at is not None else None,
            "removed_gps": data.get("removed_gps"),
        }

        return cls(**fields)


class FileData:
    """Used to upload a File to Zipline."""

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
            The MIME type of the file, if None the lib will attemp to determine it.

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

        if filename is None:
            if isinstance(data, str):
                _, filename = os.path.split(data)
            else:
                filename = getattr(data, "name", "untitled")

        self.filename = filename
        self.mimetype = mimetype or (mimetypes.guess_type(filename)[0] if filename else None)

        if self.mimetype is None:
            raise TypeError("could not determine mimetype of file given")
