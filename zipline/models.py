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

import base64
import datetime
import io
import mimetypes
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Type, Union

from .enums import FileSearchField, FileSearchSort, OAuthProviderType, Order, QuotaType, RecentFilesFilter, UserRole
from .errors import ZiplineError
from .http import HTTPClient, Route
from .utils import (
    MISSING,
    build_avatar_payload,
    generate_quota_payload,
    guess_mimetype_by_magicnumber,
    key_valid_not_none,
    parse_iso_timestamp,
)

__all__ = (
    "File",
    "Folder",
    "User",
    "InviteUser",
    "Invite",
    "TagFile",
    "Tag",
    "URL",
    "UploadFile",
    "UploadResponse",
    "FileData",
    "PartialQuota",
    "UserQuota",
    "OAuthProvider",
    "Thumbnail",
    "UserViewSettings",
    "ServerVersionInfo",
    "UserStats",
    "UserFilesResponse",
    "Avatar",
)

JSON = Union[Dict[str, Any], List[Any], int, str, float, bool, Type[None]]


@dataclass
class File:
    """
    Represents a file stored on Zipline.

    Attributes
    ----------
    id: :class:`str`
        The internal id of the file in Zipline.
    created_at: :class:`datetime.datetime`
        When the file was created.
    updated_at: :class:`datetime.datetime`
        When the file was last updated.
    deletes_at: Optional[:class:`datetime.datetime`]
        The scheduled deletion time of the file, if applicable.
    favorite: :class:`bool`
        Whether the file is favorited.
    original_name: Optional[:class:`str`]
        The original name of the file, if stored.
    name: :class:`str`
        The name of the file.
    size: :class:`int`
        The size of the file in bytes.
    type: :class:`str`
        The MIME type of the file.
    views: :class:`int`
        The number of times the file has been viewed.
    max_views: Optional[:class:`int`]
        The maximum number of times the file can be viewed before being removed, if applicable.
    password: Optional[Union[:class:`str`, :class:`bool`]]
        Whether the file is password protected.
    folder_id: Optional[:class:`str`]
        The id of the :class:`~zipline.models.Folder` that this file resides in, if applicable.
    thumbnail: Optional[:class:`~zipline.models.Thumbnail`]
        The thumbnail of the file, if available.
    tags: List[:class:`~zipline.models.Tag`]
        The tags applied to the file.
    url: Optional[:class:`str`]
        The url of this file, if given.
    """

    __slots__ = (
        "_http",
        "id",
        "created_at",
        "updated_at",
        "deletes_at",
        "favorite",
        "original_name",
        "name",
        "size",
        "type",
        "views",
        "max_views",
        "password",
        "folder_id",
        "thumbnail",
        "tags",
        "url",
    )

    _http: HTTPClient
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deletes_at: Optional[datetime.datetime]
    favorite: bool
    original_name: Optional[str]
    name: str
    size: int
    type: str
    views: int
    max_views: Optional[int]
    password: Optional[Union[str, bool]]
    folder_id: Optional[str]
    thumbnail: Optional[Thumbnail]
    tags: Optional[List[Tag]]
    url: Optional[str]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> File:
        return cls(
            http,
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            parse_iso_timestamp(data["deletesAt"]) if key_valid_not_none("deletesAt", data) else None,
            data["favorite"],
            data.get("originalName"),
            data["name"],
            data["size"],
            data["type"],
            data["views"],
            data.get("maxViews"),
            data.get("password"),
            data.get("folderId"),
            Thumbnail._from_data(data["thumbnail"]) if key_valid_not_none("thumbnail", data) else None,
            [Tag._from_data(d, http=http) for d in data["tags"]] if "tags" in data else None,
            data.get("url"),
        )

    @property
    def full_url(self) -> str:
        """
        Returns
        -------
        :class:`str`
            The full url of this file.
        """
        if self.url and (self.url.startswith("http://") or self.url.startswith("https://")):
            url = self.url
        else:
            url = f"{self._http.base_url}{self.url}"

        return url

    @property
    def thumbnail_url(self) -> Optional[str]:
        """
        Returns
        -------
        Optional[:class:`str`]
            The full url for the thumbnail image, if available.
        """
        if not self.thumbnail:
            return None

        return f"{self._http.base_url}/{self.thumbnail.path}"

    def is_password_protected(self) -> bool:
        """
        Returns the password protection status of this file.

        Returns
        -------
        :class:`bool`
        """
        return self.password is not None

    async def download_password_protected(self, password: str) -> bytes:
        """|coro|

        Download this file if password protected.

        Parameters
        ----------
        password: :class:`str`
            The password to use when accessing this file.

        Returns
        -------
        :class:`bytes`
            The content of this file.
        """
        params = {"pw": password}
        r = Route("GET", self.full_url)
        return await self._http.request(r, params=params)

    async def refresh(self) -> File:
        """|coro|

        Retrieve an updated instance of this file.

        Returns
        -------
        :class:`~zipline.models.File`
            A new instance with the latest information about this file.
        """
        r = Route("GET", f"/api/user/files/{self.id}")
        data = await self._http.request(r)
        return File._from_data(data, http=self._http)

    async def delete(self) -> File:
        """|coro|

        Delete this file.

        Returns
        -------
        :class:`~zipline.models.File`
            A new instance with the latest information about this file.
        """
        r = Route("DELETE", f"/api/user/files/{self.id}")
        data = await self._http.request(r)
        return File._from_data(data, http=self._http)

    async def edit(
        self,
        *,
        favorite: Optional[bool] = None,
        tags: Optional[Sequence[Tag]] = None,
        max_views: Optional[int] = None,
        original_name: Optional[str] = None,
        password: Optional[str] = None,
        type: Optional[str] = None,
    ) -> File:
        """|coro|

        Update this file.

        Parameters
        ----------
        favorite: Optional[:class:`bool`]
            The new favorite status of the file, if given.
        tags: Optional[Sequence[:class:`~zipline.models.Tag`]]
            Tag to apply to this file, if given.
        max_views: Optional[:class:`int`]
            The new maximum views of the file, if given.
        original_name: Optional[:class:`str`]
            The new original name of the file, if given.
        password: Optional[:class:`str`]
            The new password for the file, if given.
        type: Optional[:class:`str`]
            The new MIME type for the file, if given.

            .. warning::

                Misuse of this parameter can cause files to display incorrectly or fail outright.

        Returns
        -------
        :class:`~zipline.models.File`
            The updated file.
        """
        payload = {}

        if favorite:
            payload["favorite"] = favorite
        if tags:
            payload["tags"] = [t.id for t in tags]
        if max_views:
            payload["maxViews"] = max_views
        if original_name:
            payload["originalName"] = original_name
        if password:
            payload["password"] = password
        if type:
            payload["type"] = type

        r = Route("PATCH", f"/api/user/files/{self.id}")
        data = await self._http.request(r, json=payload)
        return File._from_data(data, http=self._http)

    async def add_favorite(self) -> File:
        """|coro|

        Favorite this file.

        Returns
        -------
        :class:`~zipline.models.File`
            A new instance with the latest information about this file.

        Raises
        ------
        ValueError
            The file is already favorited.
        """
        if self.favorite:
            raise ValueError("this file is already favorited.")

        payload = {"favorite": True}
        r = Route("PATCH", f"/api/user/files/{self.id}")
        data = await self._http.request(r, json=payload)
        return File._from_data(data, http=self._http)

    async def remove_favorite(self) -> File:
        """|coro|

        Unfavorite this file.

        Returns
        -------
        :class:`~zipline.models.File`
            A new instance with the latest information about this file.

        Raises
        ------
        ValueError
            The file is already favorited.
        """
        if not self.favorite:
            raise ValueError("this file is already not favorited.")

        payload = {"favorite": False}
        r = Route("PATCH", f"/api/user/files/{self.id}")
        data = await self._http.request(r, json=payload)
        return File._from_data(data, http=self._http)

    async def remove_from_folder(self):
        """|coro|

        Remove this file from it's current :class:`~zipline.models.Folder`.
        """
        payload = {"delete": "file", "id": self.id}
        r = Route("DELETE", f"/api/user/folders/{self.folder_id}")
        await self._http.request(r, json=payload)

    async def read(self) -> bytes:
        """|coro|

        Read the content of this file into memory.

        Returns
        -------
        :class:`bytes`
            The content of this file.
        """
        if self.url and (self.url.startswith("http://") or self.url.startswith("https://")):
            url = self.url
        else:
            url = f"{self._http.base_url}{self.url}"

        r = Route("GET", url)
        return await self._http.request(r)


@dataclass
class Folder:
    """
    Represents a Folder on Zipline.

    Attributes
    ----------
    id: :class:`str`
        The id of the folder.
    created_at: :class:`datetime.datetime`
        When the folder was created.
    updated_at: :class:`datetime.datetime`
        When the folder was last updated.
    name: :class:`str`
        The name of the folder.
    public: :class:`bool`
        Whether the folder is public.
    files: Optional[List[:class:`~zipline.models.File`]]
        The files contained in the folder, if available.
    user: Optional[:class:`~zipline.models.User`]
        The user this folder belongs to, if available.
    user_id: :class:`str`
        The id of the user this folder belongs to.
    """

    __slots__ = ("_http", "id", "created_at", "updated_at", "name", "public", "files", "user", "user_id")

    _http: HTTPClient
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: str
    public: bool
    files: Optional[List[File]]
    user: Optional[User]
    user_id: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> Folder:
        return cls(
            http,
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            data["name"],
            data["public"],
            [File._from_data(file_data, http=http) for file_data in data["files"]] if "files" in data else None,
            User._from_data(data["user"], http=http) if "user" in data else None,
            data["userId"],
        )

    async def refresh(self) -> Folder:
        """|coro|

        Retrieve an updated instance of this object.

        Returns
        -------
        :class:`~zipline.models.Folder`
            A new instance with the latest information about this folder.
        """
        r = Route("GET", f"/api/user/folders/{self.id}")
        data = await self._http.request(r)
        return Folder._from_data(data, http=self._http)

    async def delete(self) -> Folder:
        """|coro|

        Delete this folder.

        Returns
        -------
        :class:`~zipline.models.Folder`
            A new instance with the latest information about this folder.
        """
        payload = {"delete": "folder"}
        r = Route("DELETE", f"/api/user/folders/{self.id}")
        data = await self._http.request(r, json=payload)
        return Folder._from_data(data, http=self._http)

    async def edit(self, *, name: str) -> Folder:
        """|coro|

        Edit this folder.

        Parameters
        ----------
        name: :class:`str`
            The new name of this folder.

        Returns
        -------
        :class:`~zipline.models.Folder`
            The updated folder.
        """
        payload = {"name": name}
        r = Route("PATCH", f"/api/user/folders/{self.id}")
        data = await self._http.request(r, json=payload)
        return Folder._from_data(data, http=self._http)

    async def remove_file(self, file: Union[File, str], /) -> Folder:
        """|coro|

        Remove a file from this folder.

        Parameters
        ----------
        file: Union[:class:`~zipline.models.File`, :class:`str`]
            The file or file id to remove from this folder.

        Returns
        -------
        :class:`~zipline.models.Folder`
            A new instance with the latest information about this folder.
        """
        payload = {
            "delete": "file",
            "id": file.id if isinstance(file, File) else file,
        }

        r = Route("DELETE", f"/api/user/folders/{self.id}")
        data = await self._http.request(r, json=payload)
        return Folder._from_data(data, http=self._http)

    async def add_file(self, file: Union[File, str], /) -> Folder:
        """|coro|

        Add a file to this folder.

        Parameters
        ----------
        file: Union[:class:`~zipline.models.File`, :class:`str`]
            The file or file id to add to this folder.

        Returns
        -------
        :class:`~zipline.models.Folder`
            A new instance with the latest information about this folder.
        """
        payload = {"id": file.id if isinstance(file, File) else file}

        r = Route("PUT", f"/api/user/folders/{self.id}")
        data = await self._http.request(r, json=payload)
        return Folder._from_data(data, http=self._http)

    async def add_files(self, files: Sequence[Union[File, str]], /) -> Folder:
        """|coro|

        Add multiple files to this folder.

        Parameters
        ----------
        files: Sequence[Union[:class:`~zipline.models.File`, :class:`str`]]
            The files or file ids to add to this folder.

        Returns
        -------
        :class:`~zipline.models.Folder`
            A new instance with the latest information about this folder.
        """
        file_ids = [file.id if isinstance(file, File) else file for file in files]

        payload = {
            "files": file_ids,
            "folder": self.id,
        }

        r = Route("PATCH", "/api/user/files/transaction")
        data = await self._http.request(r, json=payload)
        return Folder._from_data(data, http=self._http)


@dataclass
class User:
    """
    Represents a Zipline user.

    Attributes
    ----------
    id: :class:`str`
        The id of this user.
    username: :class:`str`
        The username of this user.
    created_at: :class:`datetime.datetime`
        When this user was created or registered.
    updated_at: :class:`datetime.datetime`
        The last time this user was updated.
    role: :class:`~zipline.enums.UserRole`
        The role of this user.
    view: :class:`~zipline.models.UserViewSettings`
        Custom view info for this user.
    sessions: List[:class:`str`]
        List of session ids this user has open.
    oauth_providers: List[:class:`~zipline.models.OAuthProvider`]
        OAuth providers registered for this user.
    totp_secret: Optional[:class:`str`]
        The user's timed one-time password secret, if available.
    passkeys: List[:class:`~zipline.models.UserPasskey`]
        Passkeys registered for this user.
    quota: Optional[:class:`~zipline.models.UserQuota`]
        The quota this user has, if applicable.
    avatar: Optional[:class:`~zipline.models.Avatar`]
        The user's avatar information, if available.
    password: Optional[:class:`str`]
        Password information for this user, if available.
    token: Optional[:class:`str`]
        The user's token.
    """

    __slots__ = (
        "_http",
        "id",
        "username",
        "created_at",
        "updated_at",
        "role",
        "view",
        "sessions",
        "oauth_providers",
        "totp_secret",
        "passkeys",
        "quota",
        "avatar",
        "password",
        "token",
    )

    _http: HTTPClient
    id: str
    username: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    role: UserRole
    view: Optional[UserViewSettings]
    sessions: List[str]
    oauth_providers: List[OAuthProvider]
    totp_secret: Optional[str]
    passkeys: Optional[List[UserPasskey]]
    quota: Optional[UserQuota]
    avatar: Optional[Avatar]
    password: Optional[str]
    token: Optional[str]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> User:
        return cls(
            http,
            data["id"],
            data["username"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            UserRole(data["role"]),
            UserViewSettings._from_data(data["view"]) if key_valid_not_none("view", data) else None,
            data["sessions"],
            [OAuthProvider._from_data(d) for d in data["oauthProviders"]],
            data.get("totpSecret"),
            [UserPasskey._from_data(d) for d in data["passkeys"]] if key_valid_not_none("passkeys", data) else None,
            UserQuota._from_data(data["quota"], http=http) if key_valid_not_none("quota", data) else None,
            Avatar.from_coded_string(data["avatar"]) if key_valid_not_none("avatar", data) else None,
            data.get("password"),
            data.get("token"),
        )

    async def refresh(self) -> User:
        """|coro|

        Retrieve the latest information about this user.

        Returns
        -------
        :class:`~zipline.models.User`
            A new instance with the latest information about this user.
        """
        r = Route("GET", f"/api/users/{self.id}")
        data = await self._http.request(r)
        return User._from_data(data, http=self._http)

    async def edit(
        self,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        avatar: Optional[Avatar] = None,
        role: Optional[UserRole] = None,
        quota: Optional[Union[UserQuota, PartialQuota]] = None,
    ) -> User:
        """|coro|

        Edit this user.

        Parameters
        ----------
        username: Optional[:class:`str`]
            The new username for this user, if given.
        password: Optional[:class:`str`]
            The new password for this user, if given.
        avatar: Optional[:class:`~zipline.models.Avatar`]
            The new avatar for this user, if given.
        role: Optional[:class:`~zipline.enums.UserRole`]
            The new role for this user, if given.
        quota: Optional[Union[:class:`~zipline.models.UserQuota`, :class:`~zipline.models.PartialQuota`]]
            The new quota for this user, if given.

        Returns
        -------
        :class:`~zipline.models.User`
            The updated user.
        """
        payload = {}

        if username:
            payload["username"] = username
        if password:
            payload["password"] = password
        if avatar:
            payload["avatar"] = avatar._to_payload_str()
        if role:
            payload["role"] = role.value
        if quota:
            payload["quota"] = quota._to_dict()

        r = Route("PATCH", f"/api/users/{self.id}")
        data = await self._http.request(r, json=payload)
        return User._from_data(data, http=self._http)

    async def delete(self, *, remove_data: bool = True) -> User:
        """|coro|

        Delete this user.

        Parameters
        ----------
        remove_data: :class:`bool`
            Whether this user's files and urls should be deleted as well, by default True

        Returns
        -------
        :class:`~zipline.models.User`
            A new instance with the latest information about this user.

        Raises
        ------
        BadRequest
            Something went wrong handling the request.
        Forbidden
            You are not an administrator and cannot use this method.
        """
        payload = {"delete": remove_data}
        r = Route("DELETE", f"/api/users/{self.id}")
        data = await self._http.request(r, json=payload)
        return User._from_data(data, http=self._http)

    async def get_files(
        self,
        *,
        page: int = 1,
        per_page: int = 10,
        filter: RecentFilesFilter = RecentFilesFilter.all,
        favorite: Optional[bool] = None,
        sort_by: FileSearchSort = FileSearchSort.created_at,
        order: Order = Order.asc,
        search_field: FileSearchField = FileSearchField.file_name,
        search_query: Optional[str] = None,
    ) -> UserFilesResponse:
        """|coro|

        Get files belonging to this user.

        .. note::

            This route requires that you have an account with the Super Admin type.

        Parameters
        ----------
        page: :class:`int`
            The page of files to get.
        per_page: :class:`int`
            How many files should be returned per page.
        filter: :class:`~zipline.enums.RecentFilesFilter`
            A filter to apply to the files retrieved.
        favorite: Optional[:class:`bool`]
            Whether to search for only favorited or unfavorited files. None for all files.
        sort_by: :class:`~zipline.enums.FileSearchSort`
            How the results should be sorted. Defaults to creation datetime.
        order: :class:`~zipline.enums.Order`
            How the results should be ordered. Defaults to ascending.
        search_field: :class:`~zipline.enums.FileSearchField`
            What file attribute to search by. Defaults to file name.
        search_query: Optional[:class:`str`]
            The query to use in the search.

        Returns
        -------
        :class:`~zipline.models.UserFilesResponse`
            The requested search results.
        """
        params = {"sortBy": sort_by.value, "order": order.value, "id": self.id}

        if page:
            params["page"] = str(page)
        if per_page:
            params["perpage"] = str(per_page)
        if filter:
            params["filter"] = filter.value
        if favorite:
            params["favorite"] = "true" if favorite else "false"
        if search_field:
            params["searchField"] = search_field.value
        if search_query:
            params["searchQuery"] = search_query

        r = Route("GET", "/api/user/files")
        data = await self._http.request(r, params=params)
        return UserFilesResponse._from_data(data, http=self._http)


@dataclass
class InviteUser:
    """
    User information provided with an :class:`~zipline.models.Invite`.

    .. note::

        This can be resolved to a :class:`~zipline.models.User` via :meth:`~zipline.models.InviteUser.resolve`.

    Attributes
    ----------
    username: :class:`str`
        The username of the invite owner.
    id: :class:`str`
        The id of the invite owner.
    role: :class:`~zipline.enums.UserRole`
        The invite owner's account type.
    """

    __slots__ = ("_http", "username", "id", "role")

    _http: HTTPClient
    username: str
    id: str
    role: UserRole

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> InviteUser:
        return cls(
            http,
            data["username"],
            data["id"],
            UserRole(data["role"]),
        )

    async def resolve(self) -> User:
        """|coro|

        Resolve this object to a full :class:`~zipline.models.User`.

        Returns
        -------
        :class:`~zipline.models.User`
            The fully fledged user object.
        """
        r = Route("GET", f"/api/users/{self.id}")
        data = await self._http.request(r)
        return User._from_data(data, http=self._http)


@dataclass
class Invite:
    """
    Represents an invite to a Zipline instance.

    Attributes
    ----------
    id: :class:`str`
        The internal id of the invite.
    created_at: :class:`datetime.datetime`
        When this invite was created.
    updated_at: :class:`datetime.datetime`
        When this invite was last updated.
    expires_at: Optional[:class:`datetime.datetime`]
        When this invite expires, if applicable.
    code: :class:`str`
        The code for this invite.
    uses: :class:`int`
        The number of times this invite has been used.
    max_uses: Optional[:class:`int`]
        The number of times this invite can be used before it's no longer valid, if applicable.
    inviter: :class:`~zipline.models.InviteUser`
        The user that is attributed to the creation of this invite.
    inviter_id: :class:`str`
        The id of the user attributed to the creation of this invite.
    """

    __slots__ = (
        "_http",
        "id",
        "created_at",
        "updated_at",
        "expires_at",
        "code",
        "uses",
        "max_uses",
        "inviter",
        "inviter_id",
    )

    _http: HTTPClient
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    expires_at: Optional[datetime.datetime]
    code: str
    uses: int
    max_uses: Optional[int]
    inviter: InviteUser
    inviter_id: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> Invite:
        return cls(
            http,
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            parse_iso_timestamp(data["expiresAt"]) if key_valid_not_none("expiresAt", data) else None,
            data["code"],
            data["uses"],
            data.get("maxUses"),
            InviteUser._from_data(data["inviter"], http=http),
            data["inviterId"],
        )

    @property
    def url(self) -> str:
        """
        Returns
        -------
        :class:`str`
            The full url of this invite.
        """
        return f"{self._http.base_url}/auth/register?code={self.code}"

    async def delete(self) -> Invite:
        """|coro|

        Delete this invite.

        Returns
        -------
        :class:`~zipline.models.Invite`
            A new instance with the latest information about this invite.
        """
        r = Route("DELETE", f"/api/auth/invites/{self.id}")
        data = await self._http.request(r)
        return Invite._from_data(data, http=self._http)

    async def refresh(self) -> Invite:
        """|coro|

        Retreive updated information about this invite.

        Returns
        -------
        :class:`~zipline.models.Invite`
            A new instance with the latest information about this invite.
        """
        r = Route("GET", f"/api/auth/invites/{self.id}")
        data = await self._http.request(r)
        return Invite._from_data(data, http=self._http)


class TagFile:
    """
    Partial file given with Tags.

    .. note::

        This can be resolved to a :class:`~zipline.models.File` via :meth:`~zipline.models.TagFile.resolve`.

    Attributes
    ----------
    id: :class:`str`
        The internal id of the :class:`~zipline.models.File` represented.
    """

    __slots__ = ("_http", "id")

    def __init__(self, http: HTTPClient, id: str):
        self._http = http
        self.id = id

    async def resolve(self) -> File:
        """|coro|

        Retrieve the whole file associated with this partial data.

        Returns
        -------
        :class:`~zipline.models.File`
            The fully fledged file object.
        """
        r = Route("GET", f"/api/user/files/{self.id}")  # NOTE: Undocumented // Not officially used in the frontend.
        data = await self._http.request(r)
        return File._from_data(data, http=self._http)


@dataclass
class Tag:
    """
    Represents a tag on Zipline.

    Attributes
    ----------
    id: :class:`str`
        The internal id of the tag.
    created_at: :class:`datetime.datetime`
        When this tag was created.
    updated_at: :class:`datetime.datetime`
        When this tag was last updated.
    name: :class:`str`
        The name of this tag.
    color: :class:`str`
        The color associated with this tag.
    files: Optional[List[:class:`~zipline.models.TagFile`]]
        Partial files associated with this tag, if available.
    """

    __slots__ = ("_http", "id", "created_at", "updated_at", "name", "color", "files")

    _http: HTTPClient
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: str
    color: str
    files: Optional[List[TagFile]]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> Tag:
        return cls(
            http,
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            data["name"],
            data["color"],
            [TagFile(http, r["id"]) for r in data["files"]] if "files" in data else None,
        )

    async def edit(self, color: Optional[str] = None, name: Optional[str] = None) -> Tag:
        """|coro|

        Edit this tag.

        Parameters
        ----------
        color: Optional[:class:`str`]
            The new color of the tag, if given.

            .. note::

                Must be in hex format with preceeding #

                ex. #rrggbb
        name: Optional[:class:`str`]
            The new name of the tag, if given.

        Returns
        -------
        :class:`~zipline.models.Tag`
            The updated tag.
        """
        payload = {}

        if color:
            payload["color"] = color
        if name:
            payload["name"] = name

        r = Route("PATCH", f"/api/user/tags/{self.id}")
        data = await self._http.request(r, json=payload)
        return Tag._from_data(data, http=self._http)

    async def delete(self) -> Tag:
        """|coro|

        Delete this tag.

        Returns
        -------
        :class:`~zipline.models.Tag`
            A new instance with the latest information about this tag.
        """
        r = Route("DELETE", f"/api/user/tags/{self.id}")
        data = await self._http.request(r)
        return Tag._from_data(data, http=self._http)

    async def refresh(self) -> Tag:
        """|coro|

        Retrieve the latest information about this tag.

        Returns
        -------
        :class:`~zipline.models.Tag`
            A new instance with the latest information about this tag.
        """
        r = Route("GET", f"/api/user/tags/{self.id}")
        data = await self._http.request(r)
        return Tag._from_data(data, http=self._http)


@dataclass
class URL:
    """
    Represents a shortened url on Zipline.

    Attributes
    ----------
    id: :class:`str`
        The internal id of the url.
    created_at: :class:`datetime.datetime`
        When this url was created.
    updated_at: :class:`datetime.datetime`
        When this url was last updated.
    code: :class:`str`
        The url code.
    vanity: Optional[:class:`str`]
        The vanity code of this url, if applicable.
    destination: :class:`str`
        The url this url redirects to.
    views: :class:`int`
        The number of times this url has been used.
    max_views: Optional[:class:`int`]
        The maximum number of times this url can be used, if applicable.
    password: Optional[:class:`str`]
        The password required to use this url.
    enabled: :class:`bool`
        Whether this url is active for use.
    user: Optional[:class:`~zipline.models.User`]
        The user this url belongs to.
    user_id: :class:`str`
        The id of the user this url belongs to.
    """

    __slots__ = (
        "_http",
        "id",
        "created_at",
        "updated_at",
        "code",
        "vanity",
        "destination",
        "views",
        "max_views",
        "password",
        "enabled",
        "user",
        "user_id",
    )

    _http: HTTPClient
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    code: str  # The part of the url that redirects. <base_url>/go/<code>
    vanity: Optional[str]
    destination: str
    views: int
    max_views: Optional[int]
    password: Optional[str]
    enabled: bool
    user: Optional[User]
    user_id: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> URL:
        return cls(
            http,
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            data["code"],
            data.get("vanity"),
            data["destination"],
            data["views"],
            data.get("maxViews"),
            data.get("password"),
            data["enabled"],
            User._from_data(data["user"], http=http) if "user" in data else None,
            data["userId"],
        )

    @property
    def full_url(self) -> str:
        """
        Returns
        -------
        :class:`str`
            The full url.
        """
        code = self.vanity or self.code
        return f"{self._http.base_url}/go/{code}"

    async def edit(
        self,
        max_views: Optional[int] = None,
        vanity: Optional[str] = None,
        destination: Optional[str] = None,
        enabled: Optional[bool] = None,
        password: Optional[str] = None,
    ) -> URL:
        """|coro|

        Edit this url.

        Parameters
        ----------
        max_views: Optional[:class:`int`]
            The new maximum views, if given.
        vanity: Optional[:class:`str`]
            The new vanity code this url should have, if given.
        destination: Optional[:class:`str`]
            The new destination, if given.
        enabled: Optional[:class:`bool`]
            Whether this url should be usable, if given.
        password: Optional[:class:`str`]
            The new password required to use this url, if given.

        Returns
        -------
        :class:`~zipline.models.URL`
            The updated url.
        """
        payload = {}

        if max_views:
            payload["maxViews"] = max_views
        if vanity:
            payload["vanity"] = vanity
        if destination:
            payload["destination"] = destination
        if enabled:
            payload["enabled"] = enabled
        if password:
            payload["password"] = password

        r = Route("PATCH", f"/api/user/urls/{self.id}")
        data = await self._http.request(r, json=payload)
        return URL._from_data(data, http=self._http)

    async def delete(self) -> URL:
        """|coro|

        Delete this url.

        Returns
        -------
        :class:`~zipline.models.URL`
            A new instance with the latest information about this url.
        """
        r = Route("DELETE", f"/api/user/urls/{self.id}")
        data = await self._http.request(r)
        return URL._from_data(data, http=self._http)


@dataclass
class UploadFile:
    """
    File data given by the API when a file is uploaded.

    .. note::

        This may be resolved to a full :class:`~zipline.models.File` via :meth:`~zipline.models.UploadFile.resolve`.

    Attributes
    ----------
    id: :class:`str`
        The id of the uploaded file.
    type: :class:`str`
        The media type of the uploaded file.
    url: :class:`str`
        The url for the uploaded file.
    """

    __slots__ = ("_http", "id", "type", "url")

    _http: HTTPClient
    id: str
    type: str
    url: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> UploadFile:
        return cls(
            http,
            data["id"],
            data["type"],
            data["url"],
        )

    async def resolve(self) -> File:
        """|coro|

        Retrieve fully fledged information about this object.

        Returns
        -------
        :class:`~zipline.models.File`
            The fully fledged object
        """
        r = Route("GET", f"/api/user/files/{self.id}")  # NOTE: Undocumented // Not officially used in the frontend.
        data = await self._http.request(r)
        return File._from_data(data, http=self._http)


@dataclass
class UploadResponse:
    """
    Response given by the API when a file or multiple files are uploaded.

    Attributes
    ----------
    files: List[:class:`~zipline.models.UploadFile`]
        A list of information about the files uploaded.
    """

    __slots__ = ("_http", "files", "deletes_at")

    _http: HTTPClient
    files: List[UploadFile]
    deletes_at: Optional[datetime.datetime]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> UploadResponse:
        return cls(
            http,
            [UploadFile._from_data(uf, http=http) for uf in data["files"]],
            parse_iso_timestamp(data["deletesAt"]) if "deletesAt" in data else None,
        )


class FileData:
    """
    Used to upload a File to Zipline.

    Attributes
    ----------
    data: Union[:class:`str`, :class:`bytes`, :class:`os.PathLike`, :class:`io.BufferedIOBase`]
        The file or file like object to open.
    filename: Optional[:class:`str`]
        The name of the file to be uploaded. Defaults to filename of the given path, if applicable.
    mimetype: Optional[:class:`str`]
        The MIME type of the file, if None the lib will attempt to determine it.
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
            The MIME type of the file, if None the library will attempt to determine it.

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
            guessed_mime = guess_mimetype_by_magicnumber(self.data.read(16))
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


class PartialQuota:
    """
    A partial quota useful for creating a new quota for a :class:`~zipline.models.User`.

    Attributes
    ----------
    type: :class:`~zipline.enums.QuotaType`
        The type of this quota.
    value: Optional[:class:`int`]
        The value to assign to this quota.

        .. note::

            This may only be omitted if :attr:`~zipline.PartialQuota.type` is :attr:`~zipline.QuotaType.none`
    max_urls: Optional[int]
        The url limit for this quota.

        .. note::

            This argument may be omitted. If None is passed there will be no limit.
    """

    def __init__(self, type: QuotaType, value: Optional[int] = None, max_urls: Optional[int] = MISSING):
        if self.value and self.value < 0:
            raise ValueError("quota amount must be greater than or equal to zero.")

        if self.type is not QuotaType.none and self.value is None:
            raise ValueError("value must be given to this quota unless type is none.")

        if isinstance(max_urls, int) and max_urls <= 0:
            raise ValueError("max_urls must be greater than or equal to zero.")

        self.type = type
        self.value = value
        self.max_urls = max_urls

    def _to_dict(self) -> Dict[str, Any]:
        return generate_quota_payload(self.type, self.value, self.max_urls)


@dataclass
class UserQuota:
    """
    Represents a quota assigned to a :class:`~zipline.models.User` in Zipline.

    .. note::

        While this class may be used to update a user's quota this class is not intended
        to be created manually and should not be used for this purpose.

        Usage of :class:`~zipline.models.PartialQuota` is recommended this purpose instead.

    Attributes
    ----------
    id: :class:`str`
        The id of the quota.
    created_at: :class:`datetime.datetime`
        When this quota was created.
    updated_at: :class:`datetime.datetime`
        When this quota was last updated.
    files_quota: :class:`~zipline.enums.QuotaType`
        The type of this quota.
    max_bytes: Optional[:class:`str`]
        The maximum bytes of storage for this quota, if applicable.
    max_files: Optional[:class:`int`]
        The maximum number of files for this quota, if applicable.
    max_urls: Optional[:class:`int`]
        The maximum number of shortened urls for this quota, if applicable.
    user: Optional[:class:`~zipline.models.User`]
        The user this quota is assigned to, if given.
    user_id: Optional[:class:`str`]
        The id of the user this quota is assigned to, if given.
    """

    __slots__ = (
        "_http",
        "id",
        "created_at",
        "updated_at",
        "files_quota",
        "max_bytes",
        "max_files",
        "max_urls",
        "user",
        "user_id",
    )

    _http: HTTPClient
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    files_quota: QuotaType
    max_bytes: Optional[str]
    max_files: Optional[int]
    max_urls: Optional[int]
    user: Optional[User]
    user_id: Optional[str]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> UserQuota:
        return cls(
            http,
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            QuotaType(data["filesQuota"]),
            data.get("maxBytes"),
            data.get("maxFiles"),
            data.get("maxUrls"),
            User._from_data(data["user"], http=http) if "user" in data else None,
            data.get("userId"),
        )

    def _to_dict(self) -> Dict[str, Any]:
        return generate_quota_payload(self.type, self._amount(), self.max_urls)

    def _amount(self) -> int:
        if self.max_bytes is not None:
            return int(self.max_bytes)

        if self.max_files is not None:
            return self.max_files

        raise ValueError("amount of this quota cannot be determined.")

    @property
    def type(self) -> QuotaType:
        """
        Returns
        -------
        :class:`~zipline.enums.QuotaType`
            The type of this quota.
        """
        return self.files_quota

    async def resolve_user(self) -> User:
        """|coro|

        Resolve the user this quota is assigned to, if possible.

        Returns
        -------
        :class:`~zipline.models.User`
            The user this quota is assigned to.

        Raises
        ------
        TypeError
            The :attr:`Quota.user_id` is None and the user cannot be resolved.
        """
        if self.user_id is None:
            raise TypeError("cannot resolve user with null id.")

        r = Route("GET", f"/api/users/{self.id}")
        data = await self._http.request(r)
        return User._from_data(data, http=self._http)


@dataclass
class UserPasskey:
    """
    A passkey a Zipline :class:`~zipline.models.User` has set up.

    Attributes
    ----------
    id: :class:`str`
        The internal id of this object.
    created_at: :class:`datetime.datetime`
        When this passkey was created in the database.
    updated_at: :class:`datetime.datetime`
        When this passkey was last updated.
    last_used: Optional[:class:`datetime.datetime`]
        When this passkey was last used.
    name: :class:`str`
        The name of this passkey.
    reg: :class:`dict`
        Additional information about this passkey.
    user_id: :class:`str`
        The id of the :class:`~zipline.models.User` that this passkey belongs to.
    """

    __slots__ = ("id", "created_at", "updated_at", "last_used", "name", "reg", "user_id")

    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_used: Optional[datetime.datetime]
    name: str
    reg: JSON
    user_id: str  # NOTE: This does expose a `User` attr in the api.
    #                     Not inclined to expose it because it'd complicate this class
    #                     for minimal gain as this should already be attached to a User object.

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> UserPasskey:
        return cls(
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            parse_iso_timestamp(data["lastUsed"]) if "lastUsed" in data else None,
            data["name"],
            data["reg"],
            data["userId"],
        )


@dataclass
class OAuthProvider:
    """
    Represents an OAuth provider being used by a :class:`~zipline.models.User` on Zipline.

    Attributes
    ----------
    id: :class:`str`
        The internal id of this entry.
    created_at: :class:`datetime.datetime`
        When this entry was created.
    updated_at: :class:`datetime.datetime`
        When this entry was updated.
    user_id: :class:`str`
        The id of the user this provider registration is for.
    provider: :class:`~zipline.enums.OAuthProviderType`
        The service this entry is for.
    username: :class:`str`
        The username of this entry.
    access_token: :class:`str`
        The access token of this entry.
    refresh_token: Optional[:class:`str`]
        The refresh token for this entry.
    oauth_id: Optional[:class:`str`]
        The oauth id for this entry.
    """

    __slots__ = (
        "id",
        "created_at",
        "updated_at",
        "user_id",
        "provider",
        "username",
        "access_token",
        "refresh_token",
        "oauth_id",
    )

    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    user_id: str
    provider: OAuthProviderType
    username: str
    access_token: str
    refresh_token: Optional[str]
    oauth_id: Optional[str]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> OAuthProvider:
        return cls(
            data["id"],
            parse_iso_timestamp(data["createdAt"]),
            parse_iso_timestamp(data["updatedAt"]),
            data["userId"],
            OAuthProviderType(data["provider"]),
            data["username"],
            data["accessToken"],
            data.get("refreshToken"),
            data.get("oauthId"),
        )


class Thumbnail:
    """
    Thumbnail data for a Zipline :class:`~zipline.models.File`.

    Attributes
    ----------
    path: :class:`str`
        The path to this thumbnail.
    """

    __slots__ = ("path",)

    def __init__(self, path: str):
        self.path = path

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> Thumbnail:
        return cls(data["path"])


@dataclass
class UserViewSettings:
    """
    Represents view settings for a Zipline :class:`~zipline.models.User`.

    Attributes
    ----------
    enabled: Optional[:class:`bool`]
        Whether the view settings are enabled.
    align: Optional[Literal['left', 'center', 'right']]
        How the content should be aligned on the page.
    show_mimetype: Optional[:class:`bool`]
        Whether the content's MIME type should be displayed.
    content: Optional[:class:`str`]
        The view content.
    embed: Optional[:class:`bool`]
        Whether embed tags should be present.
    embed_title: Optional[:class:`str`]
        The title of the embed the content will generate, if applicable.
    embed_description: Optional[:class:`str`]
        The description of the embed the content will generate, if applicable.
    embed_color: Optional[:class:`str`]
        The color of the embed the content will generate, if applicable.
    embed_site_name: Optional[:class:`str`]
        The name of the site the embed will redirect to, if applicable.
    """

    __slots__ = (
        "enabled",
        "align",
        "show_mimetype",
        "content",
        "embed",
        "embed_title",
        "embed_description",
        "embed_color",
        "embed_site_name",
    )

    enabled: Optional[bool]
    align: Optional[Literal["left", "center", "right"]]
    show_mimetype: Optional[bool]
    content: Optional[str]
    embed: Optional[bool]
    embed_title: Optional[str]
    embed_description: Optional[str]
    embed_color: Optional[str]
    embed_site_name: Optional[str]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> UserViewSettings:
        return cls(
            data.get("enabled"),
            data.get("align"),
            data.get("showMimetype"),
            data.get("content"),
            data.get("embed"),
            data.get("embedTitle"),
            data.get("embedDescription"),
            data.get("embedColor"),
            data.get("embedSiteName"),
        )


@dataclass
class ServerVersionInfo:
    """
    Version information for a Zipline instance.

    Attributes
    ----------
    version: :class:`str`
        The current version being used.
    """

    __slots__ = ("version",)

    version: str

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> ServerVersionInfo:
        return cls(data["version"])


@dataclass
class UserStats:
    """
    Stats for a Zipline :class:`~zipline.models.User`.

    Attributes
    ----------
    files_uploaded: :class:`int`
        The number of files the user has uploaded.
    favorite_files: :class:`int`
        The number of files the user has favorited.
    views: :class:`int`
        The number of times files uploaded by the user have been viewed.
    avg_views: :class:`int`
        The average number of views a file uploaded by the user has received.
    storage_used: :class:`int`
        The amount of storage the user is using in bytes.
    avg_storage_used: :class:`float`
        The amount of storage a file uploaded by the user takes up in bytes.
    urls_created: :class:`int`
        The number of urls the user has created.
    url_views: :class:`int`
        The number of times urls created by the user have been visited.
    sort_type_count: Dict[:class:`str`, :class:`int`]
        A mapping of MIME type to number of files uploaded.
    """

    __slots__ = (
        "files_uploaded",
        "favorite_files",
        "views",
        "avg_views",
        "storage_used",
        "avg_storage_used",
        "urls_created",
        "url_views",
        "sort_type_count",
    )

    files_uploaded: int
    favorite_files: int
    views: int
    avg_views: int
    storage_used: int
    avg_storage_used: float
    urls_created: int
    url_views: int
    sort_type_count: Dict[str, int]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /) -> UserStats:
        return cls(
            data["filesUploaded"],
            data["favoriteFiles"],
            data["views"],
            data["avgViews"],
            data["storageUsed"],
            data["avgStorageUsed"],
            data["urlsCreated"],
            data["urlViews"],
            data["sortTypeCount"],
        )


@dataclass
class UserFilesResponse:
    """
    Represents a response to a file search on Zipline.

    Attributes
    ----------
    page: List[:class:`~zipline.models.File`]
        The files on this page.
    search: Optional[Dict[:class:`str`, Any]]
        Search parameters that were passed.
    total: Optional[:class:`int`]
        The total number of items matching the search.
    pages: Optional[:class:`int`]
        The number of pages available.
    """

    __slots__ = ("page", "search", "total", "pages")
    page: List[File]
    search: Optional[Dict[str, Any]]
    total: Optional[int]
    pages: Optional[int]

    @classmethod
    def _from_data(cls, data: Dict[str, Any], /, *, http: HTTPClient) -> UserFilesResponse:
        return cls(
            [File._from_data(d, http=http) for d in data["page"]],
            data.get("search"),
            data.get("total"),
            data.get("pages"),
        )

    @property
    def files(self) -> List[File]:
        """Alias for :attr:`~zipline.models.UserFilesResponse.page`."""
        return self.page


class Avatar:
    """
    Wraps the representation of avatars in Zipline.

    Attributes
    ----------
    data: :class:`bytes`
        The avatar data itself.
    mime: Optional[:class:`str`]
        The MIME type of the data. If not given the library will attempt to guess the type.
    """

    __slots__ = ("data", "mime")

    def __init__(self, data: bytes, mime: Optional[str] = None):
        self.data = data
        self.mime = mime or guess_mimetype_by_magicnumber(data[:16])

        if not self.mime:
            raise ZiplineError("could not determine mimetype of avatar and one was not provided.")

    @classmethod
    def from_coded_string(cls, coded_str: str) -> Avatar:
        mime_part, data = coded_str.split(";")

        mime_part = mime_part[5:]
        data = base64.b64decode(data[7:])

        return cls(data, mime_part)

    def _to_payload_str(self) -> str:
        """
        Returns the base64 encoded string for use in Zipline requests.

        Returns
        -------
        :class:`str`
            The string for use in requests.
        """
        if self.mime is None:
            raise ZiplineError("mimetype undefined in Avatar, cannot export to payload string.")

        return build_avatar_payload(self.mime, self.data)
