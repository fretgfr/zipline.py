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
from types import TracebackType
from typing import TYPE_CHECKING, AsyncGenerator, Dict, List, Literal, Optional, Sequence, Type, Union, overload

import aiohttp

from .color import Color
from .enums import FileSearchField, FileSearchSort, NameFormat, Order, RecentFilesFilter
from .http import HTTPClient, Route
from .models import (
    URL,
    Avatar,
    File,
    FileData,
    Folder,
    Invite,
    ServerVersionInfo,
    Tag,
    UploadResponse,
    User,
    UserFilesResponse,
    UserRole,
    UserStats,
    UserViewSettings,
)
from .utils import MISSING, dt_from_delta_or_dt, to_iso_format

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = ("Client",)


class Client:
    """A Zipline client.

    .. container:: operations

        .. describe:: async with x:

            Returns the client itself. Used to gracefully close the client on exit.

            .. code-block:: python3

                async with zipline.Client(server_url, token) as client:
                    ...
    """

    __slots__ = ("server_url", "http")

    def __init__(self, server_url: str, token: str) -> None:
        """Creates a new client.

        Parameters
        ----------
        server_url: :class:`str`
            The URL of the Zipline server.
        token: :class:`str`
            Your Zipline token.
        """
        self.server_url = server_url
        self.http = HTTPClient(server_url, token)

    async def get_version(self) -> ServerVersionInfo:
        """|coro|

        Gets the Zipline server version information.

        Returns
        -------
        :class:`~zipline.models.ServerVersionInfo`
            The version information for the server.
        """
        r = Route("GET", "/api/version")
        data = await self.http.request(r)
        return ServerVersionInfo._from_data(data)

    async def get_user_stats(self) -> UserStats:
        """|coro|

        Retrieve stats about the current user.

        Returns
        -------
        :class:`~zipline.models.UserStats`
            Stats for the current user.
        """
        r = Route("GET", "/api/user/stats")
        data = await self.http.request(r)
        return UserStats._from_data(data)

    async def create_user(
        self,
        *,
        username: str,
        password: str,
        role: UserRole = UserRole.user,
        avatar: Optional[Avatar] = None,
    ) -> User:
        """|coro|

        Creates a user.

        Parameters
        ----------
        username: :class:`str`
            The username of the user to create.
        password: :class:`str`
            The password of the user to create.
        role: :class:`~zipline.enums.UserRole`
            The permissions level of the created User. Only available if used by a Super Admin.
        avatar: Optional[:class:`~zipline.models.Avatar`]
            If given, an object containing the avatar to be assigned to the created user.

            .. admonition:: Example

                .. code-block:: python3

                    with open('avatar.png', 'rb') as fp:
                        avatar_bytes = fp.read()

                    avatar_mime = 'image/png'

                    avatar = zipline.Avatar(avatar_mime, avatar_bytes)

                    user = await create_user(
                        username='Example',
                        password='s0m3th!ngs3cur3',
                        avatar=avatar,
                    )

        Returns
        -------
        :class:`~zipline.models.User`
            The created user.

        Raises
        ------
        :class:`~zipline.errors.BadRequest`
            Missing required fields.
        :class:`~zipline.errors.Forbidden`
            You do not have permission to use this endpoint.
        """
        json = {"username": username, "password": password, "role": role.value}

        if avatar:
            json["avatar"] = avatar.to_payload_str()

        r = Route("POST", "/api/users")
        data = await self.http.request(r, json=json)
        return User._from_data(data, http=self.http)

    async def get_user(self, id: str, /) -> User:
        """|coro|

        Retrieve a user with given id.

        Parameters
        ----------
        id: :class:`str`
            The id of the user to get.

        Returns
        -------
        :class:`~zipline.models.User`
            The retrieved user.

        Raises
        ------
        :class:`~zipline.errors.NotFound`
            A user with that id could not be found
        """
        r = Route("GET", f"/api/users/{id}")
        data = await self.http.request(r)
        return User._from_data(data, http=self.http)

    async def get_all_users(self) -> List[User]:
        """|coro|

        Gets all users.

        Returns
        -------
        List[:class:`~zipline.models.User`]
            The retrieved users.

        Raises
        ------
        :class:`~zipline.errors.Forbidden`
            You are not an administrator and cannot use this method.
        """
        r = Route("GET", "/api/users")
        data = await self.http.request(r)
        return [User._from_data(data, http=self.http) for data in data]

    async def edit_current_user(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        avatar: Optional[Avatar] = MISSING,
        view_settings: Optional[UserViewSettings] = None,
    ) -> User:
        """|coro|

        Edit the currently authenticated user.

        .. note::

            Only provided parameters will be updated. At least one parameter must be specified.

        .. versionadded:: 0.28.0

        Parameters
        ----------
        username: Optional[:class:`str`]
            The new username for the user.
        password: Optional[:class:`str`]
            The new password for the user.
        avatar: Optional[:class:`~zipline.models.Avatar`]
            The new avatar for the user.
        view_settings: Optional[:class:`~zipline.models.UserViewSettings`]
            The new view settings for the user.

        Returns
        -------
        :class:`~zipline.models.User`
            The newly edited user model.

        Raises
        ------
        :class:`ValueError`
            No parameters were specified.
        :class:`~zipline.errors.BadRequest`
            ``username`` is already taken or any provided argument is invalid.
        """

        payload = dict()

        if username:
            payload["username"] = username

        if password:
            payload["password"] = password

        if avatar:
            payload["avatar"] = avatar.to_payload_str()

        if view_settings:
            payload["view"] = view_settings._to_payload()

        if len(payload) == 0:
            raise ValueError("at least one parameter must be specified")

        r = Route("PATCH", "/api/user")
        data = await self.http.request(r, json=payload)
        return User._from_data(data, http=self.http)

    async def delete_user(self, id, /, *, remove_data: bool = True) -> User:
        """|coro|

        Delete a user with given id.

        Parameters
        ----------
        id: :class:`str`
            The id of the user to delete.
        remove_data: :class:`bool`
            Whether the user's files and urls should be removed, by default True.

        Returns
        -------
        :class:`~zipline.models.User`
            The deleted user.

        Raises
        ------
        :class:`~zipline.errors.Forbidden`
            You are not an administrator and cannot use this method.
        """
        payload = {"delete": remove_data}
        r = Route("DELETE", f"/api/users/{id}")
        data = await self.http.request(r, json=payload)
        return User._from_data(data, http=self.http)

    async def get_all_invites(self) -> List[Invite]:
        """|coro|

        Retrieves all invites.

        .. warning::

            This method may retrieve invites for all users, not just the user the token belongs to.

        Returns
        -------
        List[:class:`~zipline.models.Invite`]
            The invites on the server.
        """
        r = Route("GET", "/api/auth/invites")
        data = await self.http.request(r)
        return [Invite._from_data(d, http=self.http) for d in data]

    async def create_invite(
        self,
        *,
        max_uses: Optional[int] = 1,
        expires_at: Optional[Union[datetime.datetime, datetime.timedelta]] = None,
    ) -> Invite:
        """|coro|

        Creates an invite.

        .. versionchanged:: 0.21.0

            Removed the count parameter as it's no longer supported.
            Return type is now a complete Invite object as opposed to a partial model.


        Parameters
        ----------
        max_uses: Optional[:class:`int`]
            The number of times the created invite can be used, by default 1.
            If None is passed the invite will have unlimited uses.

            .. versionadded:: 0.21.0
        expires_at: Optional[Union[:class:`datetime.datetime`, :class:`datetime.timedelta`]]
            When the created invite(s) should expire.

            .. versionchanged:: 0.21.0

                Default expiration removed.
                This parameter will now accept a timedelta.
                If None is passed, the invite will never expire.

        Returns
        -------
        :class:`~zipline.models.Invite`
            The created invite.

        Raises
        ------
        :class:`ValueError`
            An invalid argument was passed.
        :class:`~zipline.errors.BadRequest`
            Provided arguments are invalid.
        """
        if max_uses and not max_uses >= 1:
            raise ValueError("max_uses must be greater than or equal to 1.")

        if expires_at is None:
            expiration = "never"
        elif isinstance(expires_at, (datetime.datetime, datetime.timedelta)):
            exp = dt_from_delta_or_dt(expires_at)
            expiration = f"date={to_iso_format(exp)}"

        payload: Dict[str, Union[str, int]] = {"expiresAt": expiration}

        if max_uses is not None:
            payload["maxUses"] = max_uses

        r = Route("POST", "/api/auth/invites")
        data = await self.http.request(r, json=payload)
        return Invite._from_data(data, http=self.http)

    async def delete_invite(self, id: str, /) -> Invite:
        """|coro|

        Deletes an invite with given id.

        Parameters
        ----------
        id: :class:`str`
            The id of the invite to delete.

        Returns
        -------
        :class:`~zipline.models.Invite`
            The deleted invite.

        Raises
        ------
        :class:`~zipline.errors.NotFound`
            The id given was invalid or no longer exists.
        """
        r = Route("DELETE", f"/api/auth/invites/{id}")
        data = await self.http.request(r)
        return Invite._from_data(data, http=self.http)

    async def get_all_folders(self, *, with_files: bool = True) -> List[Folder]:
        """|coro|

        Returns all folders.

        Parameters
        ----------
        with_files: Optional[:class:`bool`]
            Whether the retrieved folder should contain file information, by default True.

        Returns
        -------
        List[:class:`~zipline.models.Folder`]
            The retrieved Folders.
        """

        params = {}
        if not with_files:
            params["noincl"] = "true"

        r = Route("GET", "/api/user/folders")
        data = await self.http.request(r, params=params)
        return [Folder._from_data(d, http=self.http) for d in data]

    async def create_folder(
        self,
        name: str,
        /,
        files: Optional[Sequence[Union[File, str]]] = None,
        public: bool = False,
    ) -> Folder:
        """|coro|

        Creates a folder.

        Parameters
        ----------
        name: :class:`str`
            The name of the folder to create.
        public: :class:`bool`
            Whether the created folder should be public, by default False.
        files: Optional[Sequence[Union[:class:`~zipline.models.File`, :class:`str`]]]
            Files that should be added to the created folder, if given.

        Returns
        -------
        :class:`~zipline.models.Folder`
            The created folder.

        Raises
        ------
        :class:`~zipline.errors.BadRequest`
            Folder name is missing or invalid. Invalid file(s) or id(s) provided.
        """
        payload = {"name": name, "isPublic": public}

        if files:
            file_ids = [file.id if isinstance(file, File) else file for file in files]
            payload["files"] = file_ids

        r = Route("POST", "/api/user/folders")
        data = await self.http.request(r, json=payload)
        return Folder._from_data(data, http=self.http)

    async def get_folder(self, id: str, /) -> Folder:
        """|coro|

        Gets a folder with given id.

        Parameters
        ----------
        id: :class:`str`
            The id of the folder to get.

        Returns
        -------
        :class:`~zipline.models.Folder`
            The requested folder.

        Raises
        ------
        :class:`~zipline.errors.NotFound`
            A folder with that id could not be found.
        """
        r = Route("GET", f"/api/user/folders/{id}")
        data = await self.http.request(r)
        return Folder._from_data(data, http=self.http)

    async def get_all_urls(self) -> List[URL]:
        """|coro|

        Retrieves all shortened urls for your user.

        Returns
        -------
        List[:class:`~zipline.models.URL`]
            The requested shortened urls.
        """
        r = Route("GET", "/api/user/urls")
        data = await self.http.request(r)
        return [URL._from_data(d, http=self.http) for d in data]

    @overload
    async def shorten_url(
        self,
        original_url: str,
        *,
        vanity: Optional[str] = ...,
        max_views: Optional[int] = ...,
        password: Optional[str] = ...,
        enabled: bool = ...,
        override_domain: Optional[Union[str, List[str]]] = ...,
        text_only: Literal[False] = ...,
    ) -> URL: ...

    @overload
    async def shorten_url(
        self,
        original_url: str,
        *,
        vanity: Optional[str] = ...,
        max_views: Optional[int] = ...,
        password: Optional[str] = ...,
        enabled: bool = ...,
        override_domain: Optional[Union[str, List[str]]] = ...,
        text_only: Literal[True] = ...,
    ) -> str: ...

    async def shorten_url(
        self,
        original_url: str,
        *,
        vanity: Optional[str] = None,
        max_views: Optional[int] = None,
        password: Optional[str] = None,
        enabled: bool = True,
        override_domain: Optional[Union[str, List[str]]] = None,
        text_only: bool = False,
    ) -> Union[URL, str]:
        """|coro|

        Shortens a url.

        Parameters
        ----------
        original_url: :class:`str`
            The url to shorten.
        vanity: Optional[:class:`str`]
            A vanity name to use. None to receive a randomly assigned name.
        max_views: Optional[:class:`int`]
            The number of times the url can be used before being deleted. None for unlimited uses, by default None.
        password: Optional[:class:`str`]
            The password required to use the URL, if given.

            .. versionadded:: 0.21.0
        enabled: :class:`bool`
            Whether the url should be enabled for use, by default True.

            .. versionadded:: 0.21.0
        override_domain: Optional[Union[:class:`str`, List[:class:`str`]]]
            The domain to return a url for. Must still be connected to the Zipline instance or it will not work.
            If a list of domains is passed, a random one will be chosen.

            .. versionadded:: 0.28.0
        text_only: :class:`bool`
            If True, return a plain text response including only the created url, by default False.

            .. versionadded:: 0.28.0

        Returns
        -------
        Union[:class:`~zipline.models.URL`, :class:`str`]
            If text_only is False, a full :class:`~zipline.models.URL` instance. Otherwise a plain
            string with the resulting url.

        Raises
        ------
        :class:`ValueError`
            Invalid value for max views passed.
        :class:`~zipline.errors.BadRequest`
            Vanity url already taken, max view invalid, destination is missing.
        :class:`~zipline.errors.Forbidden`
            Creating the URL would exceed your assigned quota.
        """
        if max_views is not None and max_views < 0:
            raise ValueError("max_views must be greater than or equal to 0")

        headers = {}

        if max_views:
            headers["X-Zipline-Max-Views"] = str(max_views)
        if password:
            headers["X-Zipline-Password"] = password
        if override_domain:
            headers["X-Zipline-Domain"] = ",".join(override_domain) if isinstance(override_domain, list) else override_domain
        if text_only:
            headers["X-Zipline-No-Json"] = "true"

        payload = {"destination": original_url, "vanity": vanity, "enabled": enabled}

        r = Route("POST", "/api/user/urls")
        data = await self.http.request(r, headers=headers, json=payload)
        return URL._from_data(data, http=self.http) if text_only is False else data

    async def delete_url(self, id: str, /) -> URL:
        """|coro|

        Delete a url by given id.

        Parameters
        ----------
        id: :class:`str`
            The id of the URL to delete.

        Returns
        -------
        :class:`~zipline.models.URL`
            The most recent information about the deleted url.

        Raises
        ------
        :class:`~zipline.errors.NotFound`
            A url with the given id could not be found.
        """
        r = Route("DELETE", f"/api/user/urls/{id}")
        data = await self.http.request(r)
        return URL._from_data(data, http=self.http)

    async def get_all_tags(self) -> List[Tag]:
        """|coro|

        Get all tags belonging to the current user.

        Returns
        -------
        List[:class:`~zipline.models.Tag`]
            The requested tags.
        """
        r = Route("GET", "/api/user/tags")
        data = await self.http.request(r)
        return [Tag._from_data(d, http=self.http) for d in data]

    async def get_tag(self, id: str, /) -> Tag:
        """|coro|

        Get a tag with given id.

        Parameters
        ----------
        id: :class:`str`
            The id of the tag to retrieve.

        Returns
        -------
        :class:`~zipline.models.Tag`
            The requested tag.

        Raises
        ------
        :class:`~zipline.errors.NotFound`
            A tag with the given id does not exist.
        """
        r = Route("GET", f"/api/user/tags/{id}")
        data = await self.http.request(r)
        return Tag._from_data(data, http=self.http)

    async def create_tag(self, name: str, *, color: Optional[Color] = None) -> Tag:
        """|coro|

        Create a tag with a given name and color.

        .. versionadded:: 0.28.0

        Parameters
        ----------
        name: str
            The name for the tag.
        color: Optional[:class:`~zipline.color.Color`]
            The color to be associated with the created tag. If not given, defaults to white.

        Returns
        -------
        :class:`~zipline.models.Tag`
            The newly created tag.

        Raises
        ------
        :class:`~zipline.errors.BadRequest`
            A tag with this name already exists.
        """
        color = color or Color.default()

        json = {
            "name": name,
            "color": color.to_hex(),
        }

        r = Route("POST", "/api/user/tags")
        data = await self.http.request(r, json=json)
        return Tag._from_data(data, http=self.http)

    async def delete_tag(self, id: str, /) -> Tag:
        """|coro|

        Delete a tag with given id.

        Parameters
        ----------
        id: :class:`str`
            The id of the tag to delete.

        Returns
        -------
        :class:`~zipline.models.Tag`
            The deleted tag.

        Raises
        ------
        :class:`~zipline.errors.NotFound`
            A tag with the given id could not be found.
        """
        r = Route("DELETE", f"/api/user/tags/{id}")
        data = await self.http.request(r)
        return Tag._from_data(data, http=self.http)

    async def get_files(
        self,
        *,
        page: int = 1,
        per_page: int = 100,
        filter: RecentFilesFilter = RecentFilesFilter.all,
        favorite: Optional[bool] = None,
        sort_by: FileSearchSort = FileSearchSort.created_at,
        order: Order = Order.asc,
        search_field: FileSearchField = FileSearchField.file_name,
        search_query: Optional[str] = None,
    ) -> UserFilesResponse:
        """|coro|

        Get files belonging to your user.

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

        Raises
        ------
        :class:`~zipline.errors.BadRequest`
            ``page`` or ``per_page`` are missing or invalid. ``sort_by``, ``order`` or ``search_field/search_query`` were invalid.
        """
        params = {"sortBy": sort_by.value, "order": order.value}

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
        data = await self.http.request(r, params=params)
        return UserFilesResponse._from_data(data, http=self.http)

    async def iter_files(
        self,
        *,
        per_page: int = 100,
        filter: RecentFilesFilter = RecentFilesFilter.all,
        favorite: Optional[bool] = None,
        sort_by: FileSearchSort = FileSearchSort.created_at,
        order: Order = Order.asc,
        search_field: FileSearchField = FileSearchField.file_name,
        search_query: Optional[str] = None,
    ) -> AsyncGenerator[File, None]:
        """
        Retrieves an :term:`asynchronous generator` of the files owned by the current user that meet the defined criteria.

        This method behaves in a similar fashion to :meth:`~zipline.client.Client.get_files`.

        .. versionadded:: 0.25.0

        .. admonition:: Example

            .. code-block:: python3

                async for file in client.iter_files():
                    if file.deletes_at:
                        print(f"{file.full_url} will be removed at: {file.deletes_at:%Y-%m-%d %H:%M:%S})

        Parameters
        ----------
        per_page: :class:`int`
            The number of results returned by each iteration, by default 100.
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

        Yields
        ------
        :class:`~zipline.models.File`
            Files that meet the search criteria.
        """

        # Uses the same args, so why not...
        async def _req_files(page_num):
            return await self.get_files(
                page=page_num,
                per_page=per_page,
                filter=filter,
                favorite=favorite,
                sort_by=sort_by,
                order=order,
                search_field=search_field,
                search_query=search_query,
            )

        res = await _req_files(1)

        for file in res.files:
            yield file

        if res.pages and res.pages > 1:
            for page_num in range(2, res.pages + 1):
                page = await _req_files(page_num)
                for file in page.files:
                    yield file

    async def get_recent_files(
        self,
        *,
        amount: int = 10,
        filter: RecentFilesFilter = RecentFilesFilter.all,
    ) -> List[File]:
        """|coro|

        Gets recent files uploaded by the current user.

        Parameters
        ----------
        amount: Optional[:class:`int`]
            The number of results to return, by default 10.
        filter: :class:`~zipline.enums.RecentFilesFilter`
            What files to get.

            .. versionchanged:: 0.21.0

                This is now controlled by an enum.

        Returns
        -------
        List[:class:`~zipline.models.File`]
            The requested Files.

        Raises
        ------
        :class:`ValueError`
            An invalid amount was passed.
        :class:`~zipline.errors.BadRequest`
            An invalid amount was passed.
        """
        if amount < 0:
            raise ValueError("amount must be greater than zero.")

        query_params = {"take": amount, "filter": filter.value}
        r = Route("GET", "/api/user/recent")
        data = await self.http.request(r, params=query_params)
        return [File._from_data(d, http=self.http) for d in data]

    async def delete_files(self, *files: Union[File, str], delete_datasource: bool = False) -> int:
        """|coro|

        Delete many files from Zipline.

        .. versionadded:: 0.28.0

        Parameters
        ----------
        files: Union[:class:`zipline.models.File`, :class:`str`]
            The files to be removed. May either be :class:`~zipline.models.File` objects or a file ids.
        delete_datasource: :class:`bool`
            Whether to delete the files from the underlying datasource as well. Defaults to False.

        Returns
        -------
        :class:`int`
            The number of deleted files.

        Raises
        ------
        :class:`~zipline.errors.BadRequest`
            Invalid file(s) or id(s) provided.
        """
        json = {
            "files": [file.id if isinstance(file, File) else file for file in files],
            "delete_datasourceFiles": "true" if delete_datasource else "false",
        }

        r = Route("DELETE", "/api/user/files/transaction")
        data = await self.http.request(r, json=json)
        return data["count"]

    async def bulk_file_favorite(self, *files: Union[File, str], favorite: bool) -> int:
        """|coro|

        Update the favorite status for many files.

        .. note::

            For bulk additions to folders, see :meth:`~zipline.models.Folder.add_files`.

        .. versionadded:: 0.28.0

        Parameters
        ----------
        files: Union[:class:`~zipline.models.File`, :class:`str`]
            The files to update favorite status for. These can be either :class:`~zipline.models.File` instances or
            strings representing the ids of the files.
        favorite: :class:`bool`
            The new favorite status.

        Returns
        -------
        :class:`int`
            The number of updated files.

        Raises
        ------
        :class:`~zipline.errors.BadRequest`
            Invalid file(s) or id(s) provided.
        :class:`~zipline.errors.NotFound`
            Specified files do not exist.
        """
        json = {
            "files": [file.id if isinstance(file, File) else file for file in files],
            "favorite": "true" if favorite else "false",
        }

        r = Route("PATCH", "/api/user/files/transaction")
        data = await self.http.request(r, json=json)
        return data["count"]

    @overload
    async def upload_file(
        self,
        *payload: FileData,
        format: Optional[NameFormat] = ...,
        compression_percent: int = ...,
        expiry: Optional[Union[datetime.datetime, datetime.timedelta]] = ...,
        password: Optional[str] = ...,
        max_views: Optional[int] = ...,
        override_name: Optional[str] = ...,
        original_name: Optional[bool] = ...,
        folder: Optional[Union[Folder, str]] = ...,
        override_extension: Optional[str] = ...,
        override_domain: Optional[Union[str, List[str]]] = ...,
        text_only: Literal[False] = ...,
    ) -> UploadResponse: ...

    @overload
    async def upload_file(
        self,
        *payload: FileData,
        format: Optional[NameFormat] = ...,
        compression_percent: int = ...,
        expiry: Optional[Union[datetime.datetime, datetime.timedelta]] = ...,
        password: Optional[str] = ...,
        max_views: Optional[int] = ...,
        override_name: Optional[str] = ...,
        original_name: Optional[bool] = ...,
        folder: Optional[Union[Folder, str]] = ...,
        override_extension: Optional[str] = ...,
        override_domain: Optional[Union[str, List[str]]] = ...,
        text_only: Literal[True] = ...,
    ) -> str: ...

    async def upload_file(
        self,
        *payload: FileData,
        format: Optional[NameFormat] = None,
        compression_percent: int = 0,
        expiry: Optional[Union[datetime.datetime, datetime.timedelta]] = None,
        password: Optional[str] = None,
        max_views: Optional[int] = None,
        override_name: Optional[str] = None,
        original_name: Optional[bool] = None,
        folder: Optional[Union[Folder, str]] = None,
        override_extension: Optional[str] = None,
        override_domain: Optional[Union[str, List[str]]] = None,
        text_only: bool = False,
    ) -> Union[UploadResponse, str]:
        """|coro|

        Upload a file to Zipline.

        Parameters
        ----------
        payload: *:class:`~zipline.models.FileData`
            Data regarding the file to upload.

            .. versionchanged:: 0.28.0

                It is now possible to pass multiple :class:`~zipline.models.FileData` objects.
        format: Optional[:class:`~zipline.enums.NameFormat`]
            The format of the name to assign to the uploaded file, uses Zipline's configured name formatting by default.

            .. versionchanged:: 0.27.0

                This parameter's default is now ``None``. Previously, it was :attr:`~zipline.enums.NameFormat.uuid`.
        compression_percent: Optional[:class:`int`]
            How compressed should the uploaded file be, by default 0.
        expiry: Optional[Union[:class:`datetime.datetime`, :class:`datetime.timedelta`]]
            When the uploaded file should expire, by default None.

            .. versionchanged:: 0.25.0

                This parameter now accepts timedeltas as well as concrete datetimes.
        password: Optional[:class:`str`]
            The password required to view the uploaded file, by default None.
        max_views: Optional[:class:`int`]
            The number of times the uploaded file can be viewed before it is deleted, by default None.
        override_name: Optional[:class:`str`]
            A name to give the uploaded file. If provided this will override the server generated name, by default None.
        original_name: Optional[:class:`bool`]
            Whether to preserve the original name of the file when downloaded.
        folder: Optional[Union[:class:`~zipline.models.Folder`, :class:`str`]]
            The folder (or it's ID) to place this upload into automatically upon completion.

            .. versionadded:: 0.15.0
        override_extension: Optional[:class:`str`]
            The extension to use for this file instead of the original.

            .. versionadded:: 0.21.0
        override_domain: Optional[Union[:class:`str`, List[:class:`str`]]]
            The domain to return a url for. Must still be connected to the Zipline instance or it will not work.
            If a list of domains is passed, a random one will be chosen.

            .. versionadded:: 0.25.0

            .. versionchanged:: 0.27.0

                It is now possible to pass a list of domains to select one at random from the list given.
        text_only: :class:`bool`
            If True this method returns a simple string containing the url of the uploaded file, by default False.

            .. versionadded:: 0.25.0

        Returns
        -------
        Union[:class:`~zipline.models.UploadResponse`, :class:`str`]
            Information about the file uploaded.

            .. versionchanged:: 0.25.0

                This now returns a :class:`str` if text_only is True.

        Raises
        ------
        :class:`ValueError`
            ``compression_percent`` was not in ``0 <= compression_percent <= 100``. ``max_views`` was less than 0.

            Type of ``folder`` is invalid.
        :class:`~zipline.errors.BadRequest`
            Provided folder does not exist.
        :class:`~zipline.errors.Forbidden`
            Folder upload not allowed for anonymous user.
        :class:`~zipline.errors.PayloadTooLarge`
            Processing this upload would exceed the quota assigned to the currently authenticated user.
        :class:`~zipline.errors.ServerError`
            An unexpected error occurred while processing the upload.
        """
        if compression_percent < 0 or compression_percent > 100:
            raise ValueError("compression_percent must be between 0 and 100")

        if max_views and max_views <= 0:
            raise ValueError("max_views must be greater than 0")

        headers = {
            "X-Zipline-Image-Compression-Percent": str(compression_percent),
        }

        if format:
            headers["X-Zipline-Format"] = format.value
        if expiry:
            exp = dt_from_delta_or_dt(expiry)
            headers["X-Zipline-Deletes-At"] = f"date={to_iso_format(exp)}"
        if password:
            headers["X-Zipline-Password"] = password
        if max_views:
            headers["X-Zipline-Max-Views"] = str(max_views)
        if override_name:
            headers["X-Zipline-Filename"] = override_name
        if original_name:
            headers["X-Zipline-Original-Name"] = "true" if original_name else "false"
        if override_extension:
            headers["X-Zipline-File-Extension"] = override_extension
        if folder:
            headers["X-Zipline-Folder"] = folder.id if isinstance(folder, Folder) else folder
        if override_domain:
            headers["X-Zipline-Domain"] = ",".join(override_domain) if isinstance(override_domain, list) else override_domain
        if text_only:
            headers["X-Zipline-No-Json"] = "true"

        formdata = aiohttp.FormData()
        for file in payload:
            formdata.add_field("file", file.data, filename=file.filename, content_type=file.mimetype)

        r = Route("POST", "/api/upload")
        data = await self.http.request(r, headers=headers, data=formdata)
        return UploadResponse._from_data(data, http=self.http) if text_only is False else data

    async def close(self) -> None:
        """|coro|

        Gracefully close the client.
        """
        await self.http.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.close()
