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
Tyre strategy plan file function
"""

from __future__ import annotations

import csv
import json
import logging

from ..setting_validator import PresetValidator
from ..userfile.json_setting import copy_setting

logger = logging.getLogger(__name__)


def set_default_tyre_setting(limited_stock: bool, starting_tread: float, wear_per_stint: float):
    return {
        "enable_limited_stock": limited_stock,
        "front_left_starting_tread":  starting_tread,
        "front_left_wear_per_stint":  wear_per_stint,
        "front_right_starting_tread": starting_tread,
        "front_right_wear_per_stint": wear_per_stint,
        "rear_left_starting_tread":   starting_tread,
        "rear_left_wear_per_stint":   wear_per_stint,
        "rear_right_starting_tread":  starting_tread,
        "rear_right_wear_per_stint":  wear_per_stint,
    }


TYRE_STRATEGY_FILE_VERSION = 1
HEADER_TYREPLAN = ("Front Left", "Front Right", "Rear Left", "Rear Right", "Change")
DEFAULT_TYRE_RULE = {
    "maximum_tyre": 4,
    "enable_restricted_allocation": True,
    "tyre_change_time_1": 4.5,
    "tyre_change_time_2": 4.5,
    "tyre_change_time_3": 12.0,
    "tyre_change_time_4": 12.0,
}
DEFAULT_TYRE_SETTING = set_default_tyre_setting(True, 100, 30)
DEFAULT_TYRE_SET = {
    "Ultrasoft": set_default_tyre_setting(True, 100, 80),
    "Supersoft": set_default_tyre_setting(True, 100, 60),
    "Soft": set_default_tyre_setting(True, 100, 40),
    "Medium": set_default_tyre_setting(True, 100, 30),
    "Hard": set_default_tyre_setting(True, 100, 20),
    "Intermediate": set_default_tyre_setting(False, 100, 40),
    "Wet": set_default_tyre_setting(False, 100, 40),
    "Q-Ultrasoft": set_default_tyre_setting(True, 80, 80),
    "Q-Supersoft": set_default_tyre_setting(True, 85, 60),
    "Q-Soft": set_default_tyre_setting(True, 90, 40),
    "Q-Medium": set_default_tyre_setting(True, 92, 30),
    "Q-Hard": set_default_tyre_setting(True, 94, 20),
    "Q-Intermediate": set_default_tyre_setting(False, 85, 40),
    "Q-Wet": set_default_tyre_setting(False, 85, 40),
}


# Tyre name formatting
def extract_tyre_key(tyre_name: str) -> str:
    """Extract tyre key from tyre name"""
    return tyre_name.split("#")[0].strip()


def encode_tyre_name(tyre_key: str, tyre_name_list: tuple[str, ...]) -> str:
    """Encode tyre key with unique tyre index (ex. 'Soft' as 'Soft #1')"""
    index = 1
    tyre_name = f"{tyre_key} #{index}"
    while tyre_name in tyre_name_list:
        index += 1
        tyre_name = f"{tyre_key} #{index}"
    return tyre_name


def decode_tyre_name(tyre_name: str) -> tuple[int, str, int]:
    """Decode tyre name (ex. 'Soft #1') to compound index, tyre (compound) key name, unique tyre index"""
    name_split = tyre_name.split("#")
    tyre_key = name_split[0].strip()
    tyre_index = int(name_split[-1])
    compound_index = 0
    for compound_index, refer_key in enumerate(DEFAULT_TYRE_SET):
        if tyre_key == refer_key:
            break
    return compound_index, tyre_key, tyre_index


def verify_tyre_name(tyre_name: str) -> bool:
    """Verify tyre name"""
    if not isinstance(tyre_name, str):
        return False
    if "#" not in tyre_name:
        return False
    name_split = tyre_name.split("#")
    if not name_split[-1].isdigit():
        return False
    if name_split[0].strip() not in DEFAULT_TYRE_SET:
        return False
    return True


# Validation function
def _validate_file_version(user_data: dict) -> int:
    """Validate file version"""
    file_version = user_data.get("file_version")
    if not isinstance(file_version, int):
        file_version = TYRE_STRATEGY_FILE_VERSION
    return file_version


def _validate_tyre_rule(user_data: dict) -> dict:
    """Validate tyre rule"""
    tyre_rule = user_data.get("tyre_rule")
    if not isinstance(tyre_rule, dict):
        tyre_rule = copy_setting(DEFAULT_TYRE_RULE)
    else:
        PresetValidator.validate_key_pair(tyre_rule, DEFAULT_TYRE_RULE)
    return tyre_rule


def _validate_tyre_set(user_data: dict) -> dict:
    """Validate tyre set (selector)"""
    tyre_set = user_data.get("tyre_set")
    if not isinstance(tyre_set, dict):
        tyre_set = copy_setting(DEFAULT_TYRE_SET)
    else:
        PresetValidator.validate_key_pair(tyre_set, DEFAULT_TYRE_SET)
        for item in tyre_set:
            PresetValidator.validate_key_pair(tyre_set[item], DEFAULT_TYRE_SET[item])
    return tyre_set


def _validate_tyre_stock(user_data: dict) -> list:
    """Validate tyre stock"""
    tyre_stock = user_data.get("tyre_stock")
    if not isinstance(tyre_stock, list):
        tyre_stock = []
    else:
        temp_set = set()  # check for duplicates
        for tyre in reversed(tyre_stock):
            # Remove invalid name
            if not verify_tyre_name(tyre) or tyre in temp_set:
                tyre_stock.remove(tyre)
                continue
            temp_set.add(tyre)
    return tyre_stock


def _validate_tyre_plan(user_data: dict, tyre_stock: list) -> list:
    """Validate tyre plan"""
    tyre_plan = user_data.get("tyre_plan")
    if not isinstance(tyre_plan, list):
        tyre_plan = []
    else:
        for tyres in reversed(tyre_plan):
            # Remove invalid row
            if not isinstance(tyres, list) or len(tyres) != 4:
                tyre_plan.remove(tyres)
                continue
            # Remove invalid name
            for index, tyre in enumerate(tyres):
                if not isinstance(tyre, str) or tyre not in tyre_stock:
                    tyres[index] = ""
    return tyre_plan


def validate_tyre_strategy(user_data: dict) -> dict:
    """Validate tyre strategy data"""
    file_version = _validate_file_version(user_data)
    tyre_rule = _validate_tyre_rule(user_data)
    tyre_set = _validate_tyre_set(user_data)
    tyre_stock = _validate_tyre_stock(user_data)
    tyre_plan = _validate_tyre_plan(user_data, tyre_stock)
    return {
        "file_version": file_version,
        "tyre_rule": tyre_rule,
        "tyre_set": tyre_set,
        "tyre_stock": tyre_stock,
        "tyre_plan": tyre_plan,
    }


# Create, load, save, export file function
def create_tyre_strategy():
    """Create new tyre strategy data"""
    return {
        "file_version": TYRE_STRATEGY_FILE_VERSION,
        "tyre_rule": copy_setting(DEFAULT_TYRE_RULE),
        "tyre_set": copy_setting(DEFAULT_TYRE_SET),
        "tyre_stock": [],
        "tyre_plan": [],
    }


def load_tyre_strategy_file(filename: str, filepath: str, extension: str = ""):
    """Load tyre strategy file (*.tyres)"""
    filename_source = f"{filepath}{filename}{extension}"
    try:
        with open(filename_source, "r", encoding="utf-8") as jsonfile:
            data = json.load(jsonfile)
            if not isinstance(data, dict):
                raise TypeError
            return validate_tyre_strategy(data)
    except FileNotFoundError:
        logger.info("USERDATA: %s not found, abort", filename)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, OSError):
        logger.error("USERDATA: %s failed loading, abort", filename)
    return None


def save_tyre_strategy_file(dict_user: dict, filename: str, filepath: str, extension: str = ""):
    """Save tyre strategy file (*.tyres)"""
    filename_source = f"{filepath}{filename}{extension}"
    with open(filename_source, "w", encoding="utf-8") as jsonfile:
        json.dump(dict_user, jsonfile, indent=2)


def export_tyre_strategy_file(
    rule_data: list,
    stock_data: list,
    plan_data: list,
    filepath: str,
    filename: str,
    extension: str = "",
) -> None:
    """Export tyre strategy file as spreadsheet (*.CSV)"""
    if len(plan_data) < 1:
        return
    with open(f"{filepath}{filename}{extension}", "w", newline="", encoding="utf-8") as csvfile:
        data_writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        # Write tyre rule
        data_writer.writerows(rule_data)
        data_writer.writerow(())
        # Write tyre stock
        data_writer.writerows(stock_data)
        data_writer.writerow(())
        # Write tyre plan
        data_writer.writerows(plan_data)
        logger.info("USERDATA: %s%s saved", filename, extension)
