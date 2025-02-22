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
)


class NameFormat(Enum):
    """Format for the name of uploaded Files"""

    original_name = "name"
    uuid = "uuid"
    date = "date"
    random = "random"
    gfycat = "gfycat"


class UserRole(Enum):
    user = "USER"
    admin = "ADMIN"
    super_admin = "SUPERADMIN"


class RecentFilesFilter(Enum):
    all = "all"
    none = "none"
    dashboard = "dashboard"


class QuotaType(Enum):
    by_bytes = "BY_BYTES"
    by_files = "BY_FILES"
    none = "NONE"  # Only applicable when editing? TODO Verify?


class OAuthProviderType(Enum):
    discord = "DISCORD"
    google = "GOOGLE"
    github = "GITHUB"
    oidc = "OIDC"
