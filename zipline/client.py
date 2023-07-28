"""
Copyright 2023 fretgfr

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

from datetime import datetime
from types import TracebackType
from typing import TYPE_CHECKING, List, Literal, Optional, Type

import aiohttp

from .enums import *
from .errors import *
from .models import *

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = ("Client",)


class Client:
    """A Zipline Client.

    Supports being created normally as well as used in an async context manager.
    """

    __slots__ = ("server_url", "_session")

    def __init__(self, server_url: str, token: str) -> None:
        """Creates a new Client.

        Parameters
        ----------
        server_url : str
            The URL of the Zipline server.
        token : str
            Your Zipline token.
        """
        self.server_url = server_url
        self._session = aiohttp.ClientSession(base_url=server_url, headers={"Authorization": token})

    async def create_user(self, *, username: str, password: str, administrator: bool = False) -> User:
        """Creates a User.

        Parameters
        ----------
        username : str
            The username of the user to create.
        password : str
            The password of the user to create.
        administrator : bool, optional
            Whether this user should be an administrator, by default False

        Returns
        -------
        User
            The created User.

        Raises
        ------
        BadRequest
            Something went wrong handling the request.
        Forbidden
            You are not an administrator and cannot use this method.
        """
        data = {"username": username, "password": password, "administrator": administrator}
        async with self._session.post("/api/auth/create", json=data) as resp:
            status = resp.status
            if status == 200:
                userdata = await resp.json()
                return User._from_data(userdata, session=self._session)
            elif status == 400:
                errdata = await resp.json()
                msg = errdata["error"]
                raise BadRequest(f"400: {msg}")
            elif status == 403:
                raise Forbidden("You cannot access this resource.")

        raise UnhandledError(f"{status} not handled in create_user!")

    async def get_password_protected_image(self, *, id: int, password: str) -> bytes:
        """Retrieves the content of a password protected File.

        Parameters
        ----------
        id : int
            The id of the File to get.
        password : str
            The password of the File to get.

        Returns
        -------
        bytes
            The File's content.

        Raises
        ------
        BadRequest
            Something went wrong handling the request.
        NotFound
            The File could not be found on the server.
        """
        query_params = {"id": id, "password": password}
        async with self._session.get("/api/auth/image", params=query_params) as resp:
            status = resp.status
            if status == 200:
                print(resp.headers)
                return await resp.read()
            elif status == 400:
                msgjson = await resp.json()
                msg = msgjson["error"]
                raise BadRequest(f"400: {msg}")
            elif status == 404:
                raise NotFound("404: Requested file not found.")

        raise UnhandledError(f"Code {status} raised in get_password_protected_image not handled!")

    async def get_all_invites(self) -> List[Invite]:
        """Retrieves all Invites.

        Returns
        -------
        List[Invite]
            The invites on the server.

        Raises
        ------
        BadRequest
            Something went wrong handling this request.
        Forbidden
            You are not an administrator and do not have permission to access this resource.
        """
        async with self._session.get("/api/auth/invite") as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return [Invite._from_data(data, session=self._session) for data in js]
            elif status == 400:
                raise BadRequest("Invites are disabled on this server")
            elif status == 403:
                raise Forbidden("You cannot access this resource.")

        raise UnhandledError(f"Code {status} unhandled in get_all_invites!")

    async def create_invites(self, *, count: int = 1, expires_at: Optional[datetime] = None) -> List[PartialInvite]:
        """Creates user invites.

        Parameters
        ----------
        count : int, optional
            The number of invites to create, by default 1
        expires_at : Optional[datetime], optional
            When the created invite(s) should expire, by default None

        Returns
        -------
        List[PartialInvite]
            The created invites.

        Raises
        ------
        ZiplineError
            The server returned the invites in an unexpected format.
        BadRequest
            The server could not process the request.
        Forbidden
            You are not an administrator and cannot use this method.
        """
        data = {"count": count, "expiresAt": f"date={expires_at.isoformat()}" if expires_at is not None else None}
        async with self._session.post("/api/auth/invite", json=data) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                # Endpoint can't return a list of invites or just a single one if you only request one
                # Endpoint *should* return a full Invite, however it only returns three fields currently,
                # hence the PartialInvite return type.
                if isinstance(js, list):
                    return [PartialInvite._from_data(data) for data in js]

                elif isinstance(js, dict):
                    return [PartialInvite._from_data(js)]

                else:
                    raise ZiplineError("Got unexpected return type on route /api/auth/invite")
            elif status == 400:
                msgjson = await resp.json()
                msg = msgjson["error"]
                raise BadRequest(f"400: {msg}")
            elif status == 403:
                raise Forbidden("You cannot access this resource.")

        raise UnhandledError(f"Code {status} unhandled in create_invites!")

    async def delete_invite(self, code: str, /) -> Invite:
        """Deletes an Invite with given code.

        Parameters
        ----------
        code : str
            The code of the Invite to delete.

        Returns
        -------
        Invite
            The deleted Invite

        Raises
        ------
        Forbidden
            You are not an administrator and cannot use this method.
        NotFound
            No Invite was found with the provided code.
        """
        query_params = {"code": code}
        async with self._session.delete("/api/auth/invite", params=query_params) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return Invite._from_data(js, session=self._session)
            elif status == 403:
                raise Forbidden("You cannot access this resource.")
            elif status == 404:
                raise NotFound(f"Could not find invite with code '{code}'")

        raise UnhandledError(f"Code {status} unhandled in delete_invite!")

    async def get_all_folders(self, *, with_files: bool = False) -> List[Folder]:
        """Returns all Folders

        Parameters
        ----------
        with_files : bool, optional
            Whether the retrieved Folder should contain File information, by default False

        Returns
        -------
        List[Folder]
            The retrieved Folders
        """
        query_params = {}
        if with_files:
            query_params["files"] = int(with_files)
        async with self._session.get("/api/user/folders", params=query_params) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return [Folder._from_data(data, session=self._session) for data in js]

        raise UnhandledError(f"Code {status} unhandled in get_all_folders!")

    async def create_folder(self, name: str, /, *, files: Optional[List[File]] = None) -> Folder:
        """Creates a Folder.

        Parameters
        ----------
        name : str
            The name of the folder to create.
        files : Optional[List[File]], optional
            Files that should be added to the created folder, by default None

        Returns
        -------
        Folder
            The created Folder

        Raises
        ------
        BadRequest
            The server could not process the request.
        """
        data = {"name": name, "add": [file.id for file in files] if files is not None else None}
        async with self._session.post("/api/user/folders", json=data) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return Folder._from_data(js, session=self._session)
            elif status == 400:
                msgjson = await resp.json()
                msg = msgjson["error"]
                raise BadRequest(f"400: {msg}")

        raise UnhandledError(f"Code {status} unhandled in create_folder!")

    async def get_folder(self, id: int, /, *, with_files: bool = False) -> Folder:
        """Gets a folder with a given id.

        Parameters
        ----------
        id : int
            The id of the folder to get.
        with_files : bool, optional
            Whether File information should be retrieved, by default False

        Returns
        -------
        Folder
            The requested Folder

        Raises
        ------
        Forbidden
            You do not have access to the Folder requested.
        NotFound
            A folder with that id could not be found.
        """
        query_params = {}
        if with_files:
            query_params["files"] = int(with_files)
        async with self._session.get(f"/api/user/folders/{id}", params=query_params) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return Folder._from_data(js, session=self._session)
            elif status == 403:
                raise Forbidden("You do not have access to that folder.")
            elif status == 404:
                raise NotFound(f"Folder with id {id} not found.")

        raise UnhandledError(f"Code {status} unhandled in create_folder!")

    async def get_user(self, id: int, /) -> User:
        """Returns a User with the given id.

        Parameters
        ----------
        id : int
            The id of the User to get.

        Returns
        -------
        User
            The retrieved User

        Raises
        ------
        Forbidden
            You are not an administrator and cannot use this method.
        NotFound
            A user with that id could not be found
        """
        async with self._session.get(f"/api/user/{id}") as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return User._from_data(js, session=self._session)
            elif status == 403:
                raise Forbidden("You cannot access this resource.")
            elif status == 404:
                raise NotFound(f"Could not find a user with id {id}")

        raise UnhandledError(f"Code {status} unhandled in get_user!")

    # TODO methods for /api/user/export

    async def get_all_files(self) -> List[File]:
        """Gets all Files belonging to your user.

        Returns
        -------
        List[File]
            The returned Files
        """
        async with self._session.get("/api/user/files") as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return [File._from_data(data, session=self._session) for data in js]

        raise UnhandledError(f"Code {status} unhandled in get_all_files !")

    # TODO BROKEN FOR SOME REASON
    async def delete_all_files(self) -> int:
        """Deletes all of your Files

        Returns
        -------
        int
            The number of removed Files
        """
        data = {"id": None, "all": True}
        async with self._session.delete("/api/user/files", json=data) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return js["count"]
            elif status >= 500:
                raise ServerError("Unhandled exception on the server.")

        raise UnhandledError(f"Code {status} unhandled in delete_all_files!")

    async def get_recent_files(self, *, amount: int = 4, filter: Literal["all", "media"] = "all") -> List[File]:
        """Gets recent files uploaded by you.

        Parameters
        ----------
        amount : int, optional
            The number of results to return. Must be in 1 <= amount <= 50, by default 4
        filter : Literal["all", "media"], optional
            What files to get. "all" to get all Files, "media" to get images/videos/etc., by default "all"

        Returns
        -------
        List[File]
            _description_

        Raises
        ------
        ValueError
            Amount was not within the specified bounds.
        """
        if amount < 1 or amount > 50:
            raise ValueError("Amount must be within 1 <= amount <= 50")

        query_params = {"take": amount, "filter": filter}
        async with self._session.get("/api/user/recent", params=query_params) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return [File._from_data(data, session=self._session) for data in js]

        raise UnhandledError(f"Code {status} unhandled in get_recent_files!")

    async def get_all_shortened_urls(self) -> List[ShortenedURL]:
        """Retrieves all shortened urls for your user.

        Returns
        -------
        List[ShortenedURL]
            The requested shortened urls.
        """
        async with self._session.get("/api/user/urls") as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return [ShortenedURL._from_data(data, session=self._session) for data in js]

        raise UnhandledError(f"Code {status} unhandled in get_all_urls!")

    async def shorten_url(
        self,
        original_url: str,
        *,
        vanity: Optional[str] = None,
        max_views: Optional[int] = None,
        zero_width_space: bool = False,
    ) -> str:
        """Shortens a url

        Parameters
        ----------
        original_url : str
            The url to shorten
        vanity : Optional[str], optional
            A vanity name to use. None to shorten normally, by default None
        max_views : Optional[int], optional
            The number of times the url can be used before being deleted. None for unlimited uses, by default None
        zero_width_space : bool, optional
            Whether to incude zero width spaces in the returned url, by default False

        Returns
        -------
        str
            The shortened url

        Raises
        ------
        ValueError
            Invalid value for max views passed.
        BadRequest
            The server could not process your request.
        NotAuthenticated
            An incorrect authorization header was passed
        """
        if max_views is not None and max_views < 0:
            raise ValueError("max_views must be greater than or equal to 0")

        headers = {"Zws": "true" if zero_width_space else "", "Max-Views": str(max_views) if max_views is not None else ""}

        data = {"url": original_url, "vanity": vanity}

        async with self._session.post("/api/shorten", headers=headers, json=data) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return js["url"]
            elif status == 400:
                msgjs = await resp.json()
                msg = msgjs["error"]
                raise BadRequest(f"400: {msg}")
            elif status == 401:
                raise NotAuthenticated("Auth header incorrect.")

        raise UnhandledError(f"Code {status} unhandled in shorten_url!")

    async def get_all_users(self) -> List[User]:
        """Gets all users.

        Returns
        -------
        List[User]
            The retrieved users

        Raises
        ------
        Forbidden
            You are not an administrator and cannot use this method.
        """
        async with self._session.get("/api/users") as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return [User._from_data(data, session=self._session) for data in js]
            elif status == 403:
                raise Forbidden("You cannot access this resource.")

        raise UnhandledError(f"Code {status} unhandled in get_all_users!")

    # TODO /api/stats methods

    # TODO /api/exif methods

    async def upload_file(
        self,
        payload: FileUploadPayload,
        *,
        format: NameFormat = NameFormat.uuid,
        compression_percent: int = 0,
        expiry: Optional[datetime] = None,
        password: Optional[str] = None,
        zero_width_space: bool = False,
        embed: bool = False,
        max_views: Optional[int] = None,
        text: bool = False,
        override_name: Optional[str] = None,
        original_name: Optional[str] = None,
    ) -> FileUploadResponse:
        """Uploads a File to zipline

        Parameters
        ----------
        payload : UploadFile
            The file to upload.
        format : NameFormat, optional
            The format of the name to assign to the uploaded File, by default NameFormat.uuid
        compression_percent : int, optional
            How compressed should the uploaded File be, by default 0
        expiry : Optional[datetime], optional
            When the uploaded File should expire, by default None
        password : Optional[str], optional
            The password required to view the uploaded File, by default None
        zero_width_space : bool, optional
            Whether to include zero width spaces in the name of the uploaded File, by default False
        embed : bool, optional
            Whether to include embed data for the uploaded File, typically used on Discord, by default False
        max_views : Optional[int], optional
            The number of times the uploaded File can be viewed before it is deleted, by default None
        text : bool, optional
            Whether the File is a text file, by default False
        override_name : Optional[str], optional
            A name to give the uploaded file. If provided this will override the server generated name, by default None
        original_name : Optional[str], optional
            The original_name of the file. None to not preserve this data, by default None

        Returns
        -------
        FileUploadResponse
            The uploaded File

        Raises
        ------
        ValueError
            compression_percent was not in 0 <= compression_percent <= 100
        ValueError
            max_views passed was less than 0
        BadRequest
            Server could not process the request
        ServerError
            The server responded with a 5xx error code.
        """
        if compression_percent < 0 or compression_percent > 100:
            raise ValueError("compression_percent must be between 0 and 100")

        if max_views and max_views < 0:
            raise ValueError("max_views must be greater than 0")

        headers = {
            "Format": format.value,
            "Image-Compression-Percent": str(compression_percent),
            "Expires-At": f"date={expiry.isoformat()}" if expiry is not None else "",
            "Password": password if password is not None else "",
            "Zws": "true" if zero_width_space else "",
            "Embed": "true" if embed else "",
            "Max-Views": str(max_views) if max_views is not None else "",
            "UploadText": "true" if text else "",
            "X-Zipline-Filename": override_name if override_name is not None else "",
            "Original-Name": original_name if original_name is not None else "",
        }

        formdata = aiohttp.FormData()
        formdata.add_field("file", payload.data, filename=payload.filename, content_type=payload.mimetype)

        async with self._session.post("/api/upload", headers=headers, data=formdata) as resp:
            status = resp.status
            if status == 200:
                js = await resp.json()
                return FileUploadResponse._from_data(js)

            elif status == 400:
                js = await resp.json()
                err_message = js["error"]
                raise BadRequest(f"400: {err_message}")

            elif status >= 500:
                raise ServerError(f"Server responded with a {status} response code.")

        raise UnhandledError(f"Code {status} not handled in upload_file!")

    async def close(self) -> None:
        """Gracefully close the client."""
        await self._session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.close()
