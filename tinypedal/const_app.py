#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Constants
"""

import platform

from . import version_check
from .userfile import set_global_user_path

# System info
PLATFORM = platform.system()

# App version
VERSION = version_check.tinypedal()

# App info
APP_NAME = "TinyPedal"
REPO_NAME = "TinyPedal/TinyPedal"
COPYRIGHT = "Copyright (C) 2022-2025 TinyPedal developers"
DESCRIPTION = "Free and Open Source telemetry overlay application for racing simulation."
LICENSE = "Licensed under the GNU General Public License v3.0 or later."

# URL
URL_WEBSITE = f"https://github.com/{REPO_NAME}"
URL_USER_GUIDE = f"{URL_WEBSITE}/wiki/User-Guide"
URL_FAQ = f"{URL_WEBSITE}/wiki/Frequently-Asked-Questions"
URL_RELEASE = f"{URL_WEBSITE}/releases"

# Global path
PATH_GLOBAL = set_global_user_path(APP_NAME, PLATFORM)
