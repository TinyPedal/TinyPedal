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
Heatmap function
"""

from __future__ import annotations

import re

from .regex_pattern import COMMON_TYRE_COMPOUNDS
from .setting import ConfigType, cfg
from .template.setting_heatmap import HEATMAP_DEFAULT_BRAKE, HEATMAP_DEFAULT_TYRE
from .validator import invalid_save_name, is_hex_color


# Brake function
def add_missing_brake(brake_name: str) -> None:
    """Add missing brake style to brakes preset"""
    cfg.user.brakes[brake_name] = {
        "failure_thickness": 0.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    }
    cfg.save(cfg_type=ConfigType.BRAKES)


def set_predefined_brake_name(class_name: str, is_front: bool) -> str:
    """Set common brake name"""
    if is_front:
        return f"{class_name} - Front Brake"
    return f"{class_name} - Rear Brake"


def select_brake_failure_thickness(brake_name: str) -> float:
    """Select brake failure thickness, minimum thickness 0.0"""
    brake = cfg.user.brakes.get(brake_name, None)
    if brake is not None:
        return max(brake.get("failure_thickness", 0.0), 0)
    if not invalid_save_name(brake_name):
        add_missing_brake(brake_name)
    return 0.0


def select_brake_heatmap_name(brake_name: str) -> str:
    """Select brake heatmap name from brakes preset"""
    brake = cfg.user.brakes.get(brake_name, None)
    if brake is None:
        if invalid_save_name(brake_name):
            return HEATMAP_DEFAULT_BRAKE
        add_missing_brake(brake_name)
        brake = cfg.user.brakes.get(brake_name)
    return brake.get("heatmap", HEATMAP_DEFAULT_BRAKE)


# Tyre function
def add_missing_compound(compound_name: str) -> None:
    """Add missing compound style to compounds preset"""
    cfg.user.compounds[compound_name] = {
        "symbol": set_predefined_compound_symbol(compound_name),
        "heatmap": HEATMAP_DEFAULT_TYRE,
    }
    cfg.save(cfg_type=ConfigType.COMPOUNDS)


def set_predefined_compound_symbol(compound_name: str) -> str:
    """Set common tyre compound name to predefined symbol"""
    for compound in COMMON_TYRE_COMPOUNDS:
        if re.search(compound[0], compound_name, flags=re.IGNORECASE):
            return compound[1]
    return "?"


def select_compound_symbol(compound_name: str) -> str:
    """Select compound symbol"""
    compound = cfg.user.compounds.get(compound_name, None)
    if compound is not None:
        return compound.get("symbol", "?")
    if not invalid_save_name(compound_name):
        add_missing_compound(compound_name)
    return set_predefined_compound_symbol(compound_name)


def select_tyre_heatmap_name(compound_name: str) -> str:
    """Select tyre heatmap name from compounds preset"""
    compound = cfg.user.compounds.get(compound_name, None)
    if compound is None:
        if invalid_save_name(compound_name):
            return HEATMAP_DEFAULT_TYRE
        add_missing_compound(compound_name)
        compound = cfg.user.compounds.get(compound_name)
    return compound.get("heatmap", HEATMAP_DEFAULT_TYRE)


# Heatmap function
def verify_heatmap(heatmap_dict: dict | None) -> bool:
    """Verify color in heatmap"""
    if not heatmap_dict:
        return False
    for color in heatmap_dict.values():
        if not is_hex_color(color):
            return False
    return True


def load_heatmap(heatmap_name: str, default_name: str) -> list[tuple[float, str]]:
    """Load heatmap preset (dictionary)

    key = temperature string, value = hex color string.
    Convert key to float, sort by key.

    Args:
        heatmap_name: heatmap preset name.
        default_name: default preset name.

    Returns:
        list(tuple(temperature value, hex color string))
    """
    heatmap_dict = cfg.user.heatmap.get(heatmap_name, None)
    if not verify_heatmap(heatmap_dict):
        heatmap_dict = cfg.default.heatmap[default_name]
    return sorted(
        (float(temp), heatmap_color)
        for temp, heatmap_color in heatmap_dict.items()
    )


def load_heatmap_style(
    heatmap_name: str, default_name: str, swap_style: bool = False,
    fg_color: str = "", bg_color: str = "") -> list[tuple[float, str]]:
    """Load heatmap preset (dictionary) & set color style sheet

    key = temperature string, value = hex color string.
    Convert key to float, sort by key.

    Args:
        heatmap_name: heatmap preset name.
        default_name: default preset name.
        swap_style: assign heatmap color as background color if True, otherwise as foreground.
        fg_color: assign foreground color if swap_style True.
        bg_color: assign background color if swap_style False.

    Returns:
        list(tuple(temperature value, color style sheet string))
    """
    heatmap_dict = cfg.user.heatmap.get(heatmap_name, None)
    if not verify_heatmap(heatmap_dict):
        heatmap_dict = cfg.default.heatmap[default_name]
    if swap_style:
        return sorted(
            (float(temp), f"color:{fg_color};background:{heatmap_color};")
            for temp, heatmap_color in heatmap_dict.items()
        )
    return sorted(
        (float(temp), f"color:{heatmap_color};background:{bg_color};")
        for temp, heatmap_color in heatmap_dict.items()
    )
