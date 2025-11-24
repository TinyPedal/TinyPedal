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
Heatmap preset function
"""

from __future__ import annotations

import re

from ..const_file import ConfigType
from ..regex_pattern import COMMON_TYRE_COMPOUNDS
from ..setting import cfg
from ..template.setting_brakes import BRAKEINFO_DEFAULT
from ..template.setting_compounds import COMPOUNDINFO_DEFAULT
from ..template.setting_heatmap import HEATMAP_DEFAULT_BRAKE, HEATMAP_DEFAULT_TYRE
from ..validator import invalid_save_name, is_hex_color


# Brake function
def add_missing_brake(brake_name: str) -> dict:
    """Add missing brake style to brakes preset"""
    new_data = BRAKEINFO_DEFAULT.copy()
    cfg.user.brakes[brake_name] = new_data
    cfg.save(cfg_type=ConfigType.BRAKES)
    return new_data


def save_brake_failure_thickness(brake_name: str, failure: float) -> None:
    """Save brake failure thickness (mm) to brakes preset when brake fails"""
    if invalid_save_name(brake_name):
        return
    brake = cfg.user.brakes.get(brake_name)
    if brake is None:
        new_data = BRAKEINFO_DEFAULT.copy()
        new_data["failure_thickness"] = failure
        cfg.user.brakes[brake_name] = new_data
    else:
        brake["failure_thickness"] = failure
    cfg.save(cfg_type=ConfigType.BRAKES)


def set_predefined_brake_name(class_name: str, vehicle_name: str, is_front: bool) -> str:
    """Set common brake name"""
    if class_name == "":
        return ""
    suffix_name = "Front Brake" if is_front else "Rear Brake"
    brand_name = cfg.user.brands.get(vehicle_name, "")
    if brand_name != "":
        return f"{class_name} - {brand_name} {suffix_name}"
    return f"{class_name} - {suffix_name}"


def select_brake_failure_thickness(brake_name: str) -> float:
    """Select brake failure thickness, minimum thickness 0.0"""
    brake = cfg.user.brakes.get(brake_name)
    if brake is not None:
        return max(brake.get("failure_thickness", 0.0), 0.0)
    if not invalid_save_name(brake_name):
        add_missing_brake(brake_name)
    return 0.0


def select_brake_heatmap_name(brake_name: str) -> str:
    """Select brake heatmap name from brakes preset"""
    brake = cfg.user.brakes.get(brake_name)
    if brake is None:
        if invalid_save_name(brake_name):
            return HEATMAP_DEFAULT_BRAKE
        brake = add_missing_brake(brake_name)
    return brake.get("heatmap", HEATMAP_DEFAULT_BRAKE)


def brake_failure_thickness(class_name: str, vehicle_name: str) -> tuple[float, float, float, float]:
    """Get failure thickness"""
    failure_thickness_f = select_brake_failure_thickness(
        set_predefined_brake_name(class_name, vehicle_name, True)
    )
    failure_thickness_r = select_brake_failure_thickness(
        set_predefined_brake_name(class_name, vehicle_name, False)
    )
    return (
        failure_thickness_f,
        failure_thickness_f,
        failure_thickness_r,
        failure_thickness_r,
    )


# Tyre function
def add_missing_compound(compound_name: str) -> dict:
    """Add missing compound style to compounds preset"""
    new_data = COMPOUNDINFO_DEFAULT.copy()
    new_data["symbol"] = set_predefined_compound_symbol(compound_name)
    cfg.user.compounds[compound_name] = new_data
    cfg.save(cfg_type=ConfigType.COMPOUNDS)
    return new_data


def set_predefined_compound_symbol(compound_name: str) -> str:
    """Set common tyre compound name to predefined symbol"""
    for compound in COMMON_TYRE_COMPOUNDS:
        if re.search(compound[0], compound_name, flags=re.IGNORECASE):
            return compound[1]
    return "?"


def select_compound_symbol(compound_name: str) -> str:
    """Select compound symbol"""
    compound = cfg.user.compounds.get(compound_name)
    if compound is not None:
        return compound.get("symbol", "?")
    if not invalid_save_name(compound_name):
        add_missing_compound(compound_name)
    return set_predefined_compound_symbol(compound_name)


def select_tyre_heatmap_name(compound_name: str) -> str:
    """Select tyre heatmap name from compounds preset"""
    compound = cfg.user.compounds.get(compound_name)
    if compound is None:
        if invalid_save_name(compound_name):
            return HEATMAP_DEFAULT_TYRE
        compound = add_missing_compound(compound_name)
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


def load_heatmap_style(
    heatmap_name: str, default_name: str, swap_style: bool = False,
    fg_color: str = "", bg_color: str = "") -> tuple[tuple[float, str], ...]:
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
        tuple(tuple(temperature value, color style sheet string))
    """
    heatmap_dict = cfg.user.heatmap.get(heatmap_name)
    if not verify_heatmap(heatmap_dict):
        heatmap_dict = cfg.default.heatmap[default_name]
    if swap_style:
        return tuple(sorted(
            (float(temp), f"color:{fg_color};background:{heatmap_color};")
            for temp, heatmap_color in heatmap_dict.items()
        ))
    return tuple(sorted(
        (float(temp), f"color:{heatmap_color};background:{bg_color};")
        for temp, heatmap_color in heatmap_dict.items()
    ))


#def load_heatmap(heatmap_name: str, default_name: str) -> list[tuple[float, str]]:
#    """Load heatmap preset (dictionary)
#
#    key = temperature string, value = hex color string.
#    Convert key to float, sort by key.
#
#    Args:
#        heatmap_name: heatmap preset name.
#        default_name: default preset name.
#
#    Returns:
#        list(tuple(temperature value, hex color string))
#    """
#    heatmap_dict = cfg.user.heatmap.get(heatmap_name)
#    if not verify_heatmap(heatmap_dict):
#        heatmap_dict = cfg.default.heatmap[default_name]
#    return sorted(
#        (float(temp), heatmap_color)
#        for temp, heatmap_color in heatmap_dict.items()
#    )
