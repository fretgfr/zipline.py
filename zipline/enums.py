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

from enum import Enum

__all__ = (
    "NameFormat",
    "UserRole",
    "RecentFilesFilter",
    "QuotaType",
    "OAuthProviderType",
    "Order",
    "FileSearchField",
    "FileSearchSort",
)


class NameFormat(str, Enum):
    """Format for the name of uploaded files."""

    original_name = "name"
    uuid = "uuid"
    date = "date"
    random = "random"
    gfycat = "gfycat"


class UserRole(str, Enum):
    """The role of a Zipline user."""

    user = "USER"
    admin = "ADMIN"
    super_admin = "SUPERADMIN"


class RecentFilesFilter(str, Enum):
    """Filters that apply to recent files requests."""

    all = "all"
    none = "none"
    dashboard = "dashboard"


class QuotaType(str, Enum):
    """The different types of quotas that can be applied to a user."""

    by_bytes = "BY_BYTES"
    by_files = "BY_FILES"
    none = "NONE"


class OAuthProviderType(str, Enum):
    """Supported types of OAuth providers."""

    discord = "DISCORD"
    google = "GOOGLE"
    github = "GITHUB"
    oidc = "OIDC"


class Order(str, Enum):
    """Ordering of returned results."""

    asc = "asc"
    desc = "desc"


class FileSearchField(str, Enum):
    """Fields that can be searched by."""

    original_name = "originalName"
    type = "type"
    tags = "tags"
    id = "id"
    file_name = "name"


class FileSearchSort(str, Enum):
    """Fields that files can be ordered by."""

    id = "id"
    created_at = "createdAt"
    updated_at = "updatedAt"
    deletes_at = "deletesAt"
    file_name = "name"
    original_name = "originalName"
    size = "size"
    type = "type"
    views = "views"
    favorite = "favorite"
