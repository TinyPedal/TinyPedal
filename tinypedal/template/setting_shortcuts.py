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

from __future__ import annotations

from types import MappingProxyType

from ..template.setting_module import MODULE_FILENAME
from ..template.setting_widget import WIDGET_FILENAME

SHORTCUT_DEFAULT = MappingProxyType({
    "bind": "",
})


def generate_shortcut_setting(source: tuple[str], prefix: str = "") -> dict:
    """Generate shortcut setting"""
    if not prefix:
        return {name: SHORTCUT_DEFAULT.copy() for name in source}
    return {f"{prefix}_{name}": SHORTCUT_DEFAULT.copy() for name in source}


SHORTCUTS_WIDGET = generate_shortcut_setting(WIDGET_FILENAME, "widget")
SHORTCUTS_MODULE = generate_shortcut_setting(MODULE_FILENAME)
SHORTCUTS_GENERAL = generate_shortcut_setting(
    (
        "overlay_visibility",
        "overlay_lock",
        "vr_compatibility",
        "restart_api",
        "select_next_api",
        "select_previous_api",
        "reload_preset",
        "load_next_preset",
        "load_previous_preset",
        "spectate_mode",
        "spectate_next_driver",
        "spectate_previous_driver",
        "pace_notes_playback",
        "restart_application",
        "quit_application",
    )
)
