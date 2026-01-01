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
Version check function
"""

from __future__ import annotations

import sys

from .const_common import VERSION_NA


def parse_version_string(ver: str) -> tuple[int, int, int]:
    """Parse version string to tuple (major, minor, patch)"""
    try:
        version = ver.split(".")
        return int(version[0]), int(version[1]), int(version[2])
    except (AttributeError, ValueError, TypeError, IndexError):
        return 0, 0, 0


def is_new_version(
    checked_version: tuple[int, int, int],
    current_version: tuple[int, int, int],
    version_tag: str,
) -> bool:
    """Is new version"""
    # Invalid version
    if checked_version == VERSION_NA:
        return False
    # New version
    if checked_version > current_version:
        return True
    # Pre-release version
    if checked_version == current_version and version_tag:
        return True
    # Same version
    return False


def tinypedal() -> str:
    from . import version

    ver_number = (version.__version__, version.DEVELOPMENT)
    return "-".join(ver for ver in ver_number if ver != "")


def python() -> str:
    return ".".join(map(str, sys.version_info))


def qt() -> str:
    from PySide2.QtCore import qVersion

    return qVersion()


def pyside() -> str:
    import PySide2

    return PySide2.__version__


def psutil() -> str:
    import psutil

    return psutil.__version__
