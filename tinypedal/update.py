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
Check for updates
"""

from __future__ import annotations

import asyncio
import logging
import threading

from . import overlay_signal, version
from .async_request import get_response, set_header_get
from .const_app import APP_NAME, REPO_NAME

VERSION_NA = (0, 0, 0)  # major, minor, patch
DATE_NA = VERSION_NA  # year, month, day
logger = logging.getLogger(__name__)


def request_latest_release():
    """Setup request for latest release data from github Rest API"""
    uri_path = f"/repos/{REPO_NAME}/releases/latest"
    host = "api.github.com"
    port = 443
    timeout = 5
    user_agent = f"User-Agent: {APP_NAME}/{version.__version__}"
    request_header = set_header_get(
        uri_path,
        host,
        user_agent,
        "Accept: application/vnd.github+json",
        "X-GitHub-Api-Version: 2022-11-28",
    )
    return get_response(request_header, host, port, timeout, ssl=True)


def parse_version(data: bytes) -> tuple[int, int, int]:
    """Parse release version"""
    try:
        pos_beg = data.find(b'"', data.find(b":", data.find(b"tag_name"))) + 1
        if pos_beg > 0:
            pos_end = data.find(b'"', pos_beg)
            ver_raw = data[pos_beg:pos_end]
            ver_strip = ver_raw.lstrip(b"v").split(b"-")[0]
            ver_split = ver_strip.split(b".")
            return int(ver_split[0]), int(ver_split[1]), int(ver_split[2])
    except (AttributeError, TypeError, IndexError, ValueError):
        logger.error("UPDATES: error while fetching latest release version info")
    return VERSION_NA


def parse_date(data: bytes) -> tuple[int, int, int]:
    """Parse release date"""
    try:
        pos_beg = data.find(b'"', data.find(b":", data.find(b"published_at"))) + 1
        if pos_beg > 0:
            pos_end = data.find(b'"', pos_beg)
            date_raw = data[pos_beg:pos_end]
            date_strip = date_raw.strip().split(b"T")[0]
            date_split = date_strip.split(b"-")
            return int(date_split[0]), int(date_split[1]), int(date_split[2])
    except (AttributeError, TypeError, IndexError, ValueError):
        logger.error("UPDATES: error while fetching latest release date info")
    return DATE_NA


class UpdateChecker:
    """Check for updates"""

    __slots__ = (
        "_is_checking",
        "_update_available",
        "_manual_checking",
        "_last_checked_version",
        "_last_checked_date",
    )

    def __init__(self):
        self._is_checking = False
        self._update_available = False
        self._manual_checking = False
        self._last_checked_version = VERSION_NA
        self._last_checked_date = DATE_NA

    def is_manual(self) -> bool:
        """Is manual checking"""
        return self._manual_checking

    def is_updates(self) -> bool:
        """Is updates available"""
        return self._update_available

    def check(self, manual: bool):
        """Run update check in separated thread"""
        self._manual_checking = manual
        if not self._is_checking:
            self._is_checking = True
            overlay_signal.updates.emit(True)
            threading.Thread(target=self.__checking, daemon=True).start()

    def __checking(self):
        """Fetch version info from github Rest API"""
        raw_bytes = asyncio.run(request_latest_release())
        checked_version = parse_version(raw_bytes)
        checked_date = parse_date(raw_bytes)
        current_version = tuple(map(int, version.__version__.split(".")))
        # Output log
        if checked_version == VERSION_NA:
            self._update_available = False
            logger.info("UPDATES: Unable To Find Updates")
        elif checked_version > current_version or (
            checked_version == current_version and version.DEVELOPMENT  # pre-release version check
        ):
            self._update_available = True
            logger.info(
                "UPDATES: New Updates: v%s.%s.%s (%s-%s-%s)",
                *checked_version,
                *checked_date,
            )
        else:
            self._update_available = False
            logger.info("UPDATES: No Updates Available")
        # Save info
        self._last_checked_version = checked_version
        self._last_checked_date = checked_date
        # Send update signal
        overlay_signal.updates.emit(False)
        self._is_checking = False

    def message(self) -> str:
        """Get message"""
        if self._last_checked_version == VERSION_NA:
            return "Unable To Find Updates"
        if not self._update_available:
            return "No Updates Available"
        return "New Updates: v{0}.{1}.{2} ({3}-{4}-{5})".format(
            *self._last_checked_version,
            *self._last_checked_date,
        )


update_checker = UpdateChecker()
