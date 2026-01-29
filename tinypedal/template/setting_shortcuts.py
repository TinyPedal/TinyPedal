#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2026 TinyPedal developers, see contributors.md file
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
Default keyboard shortcuts template
"""

from types import MappingProxyType

from ..const_module import MODULE_FILENAME
from ..const_widget import WIDGET_FILENAME

SHORTCUT_DEFAULT = MappingProxyType({
    "bind": "",
})


def generate_setting(source: tuple, prefix: str):
    if not prefix:
        return {name: SHORTCUT_DEFAULT.copy() for name in source}
    return {f"{prefix}_{name}": SHORTCUT_DEFAULT.copy() for name in source}


SHORTCUTS_WIDGET = generate_setting(WIDGET_FILENAME, "widget")
SHORTCUTS_MODULE = generate_setting(MODULE_FILENAME, "")
SHORTCUTS_GENERAL = {
    "overlay_visibility": {
        "bind": "",
    },
    "overlay_lock": {
        "bind": "",
    },
    "vr_compatibility": {
        "bind": "",
    },
    "restart_api": {
        "bind": "",
    },
    "select_next_api": {
        "bind": "",
    },
    "select_previous_api": {
        "bind": "",
    },
    "reload_preset": {
        "bind": "",
    },
    "load_next_preset": {
        "bind": "",
    },
    "load_previous_preset": {
        "bind": "",
    },
    "spectate_mode": {
        "bind": "",
    },
    "spectate_next_driver": {
        "bind": "",
    },
    "spectate_previous_driver": {
        "bind": "",
    },
    "pace_notes_playback": {
        "bind": "",
    },
    "restart_application": {
        "bind": "",
    },
    "quit_application": {
        "bind": "",
    },
}
