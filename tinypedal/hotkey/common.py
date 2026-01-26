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
Hotkey function
"""

from __future__ import annotations

from typing import Callable, Mapping

from ..const_app import PLATFORM
from .keymap import KEYMAP_GENERAL, KEYMAP_MODIFIER


def format_hotkey_name(name: str, notset: str = "", delimiter: str = "+") -> str:
    """Format hotkey name for display"""
    return name.replace("_", " ").replace("+", delimiter).title() if name else notset


def modifier_priority(key: str) -> int:
    """Get modifier key priority - 0=ctrl, 1=shift, 2=alt"""
    if "ctrl" in key:
        return 0
    if "shift" in key:
        return 1
    if "alt" in key:
        return 2
    return 0


def get_key_state_function() -> Callable[[int], int]:
    """Platform specific 'get key state' function"""
    if PLATFORM == "Windows":
        from ctypes import windll

        return windll.user32.GetAsyncKeyState
    return _get_key_state_linux


def refresh_keystate(get_key_state: Callable[[int], int]) -> None:
    """Refresh and clean up key state - Windows"""
    if PLATFORM == "Windows":
        _refresh_keystate_win(get_key_state)
    else:
        _refresh_keystate_linux(get_key_state)


def validate_hotkey(
    key_string: str,
    key_general: Mapping[str, int] = KEYMAP_GENERAL,
    key_modifier: Mapping[str, int] = KEYMAP_MODIFIER,
    delimiter: str = "+",
) -> str:
    """Validate hotkey from string - ex. 'ctrl+alt+space' is valid"""
    if not key_string:
        return key_string
    key_split = key_string.split(delimiter)
    max_index = len(key_split) - 1
    output_combo = []
    for idx, key in enumerate(key_split):
        if idx < max_index:  # get modifier (optional)
            if key not in key_modifier:
                continue
        else:  # get general key (invalid if not found)
            if key not in key_general:
                return ""
        output_combo.append(key)
    return "+".join(output_combo)


def load_hotkey(
    key_string: str,
    key_general: Mapping[str, int] = KEYMAP_GENERAL,
    key_modifier: Mapping[str, int] = KEYMAP_MODIFIER,
    delimiter: str = "+",
) -> tuple[int, ...]:
    """Load hotkey string and export as key code sequence"""
    key_split = key_string.split(delimiter)
    max_index = len(key_split) - 1
    output_combo = []
    for idx, key in enumerate(key_split):
        if idx < max_index:
            code = key_modifier.get(key)
            if code is None:
                continue
        else:
            code = key_general.get(key)
            if code is None:  # invalid combo
                return ()
        output_combo.append(code)
    return tuple(output_combo)


def set_hotkey_win(
    get_key_state: Callable,
    key_general: Mapping[str, int] = KEYMAP_GENERAL,
    key_modifier: Mapping[str, int] = KEYMAP_MODIFIER,
) -> tuple[str, ...]:
    """Set hotkey string"""
    key_combo = [""] * 4  # Ctrl, Alt, Shift, Key
    # Key state: 0=off, 1=pressed, <1=down
    # Assign mod key
    for key, code in key_modifier.items():
        priority = modifier_priority(key)
        if get_key_state(code) != 0:
            key_combo[priority] = key
        else:  # remove if not pressed
            key_combo[priority] = ""
    # Assign common key
    for key, code in key_general.items():
        if get_key_state(code) != 0:
            key_combo[-1] = key
            return tuple(key_combo)
    return ()


# Private
def _get_key_state_linux(key_code: int) -> int:
    """Get key state - Linux (placeholder)"""
    return 0


def _refresh_keystate_win(get_key_state: Callable[[int], int]) -> None:
    """Refresh and clean up key state - Windows"""
    for idx in range(255):
        get_key_state(idx)


def _refresh_keystate_linux(get_key_state: Callable[[int], int]) -> None:
    """Refresh and clean up key state - Linux (placeholder)"""
    pass
