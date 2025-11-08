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
Setting validator function
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from . import regex_pattern as rxp
from .template.setting_brakes import BRAKEINFO_DEFAULT
from .template.setting_classes import CLASSINFO_DEFAULT
from .template.setting_compounds import COMPOUNDINFO_DEFAULT
from .template.setting_filelock import FILELOCKINFO_DEFAULT
from .template.setting_tracks import TRACKINFO_DEFAULT
from .validator import is_clock_format, is_hex_color

COMMON_STRINGS = "|".join((
    rxp.CFG_FONT_NAME,
    rxp.CFG_HEATMAP,
    rxp.CFG_USER_PATH,
    rxp.CFG_USER_IMAGE,
    rxp.CFG_STRING,
))


def validate_style(dict_user: dict[str, dict], dict_def: Mapping[str, Any]) -> bool:
    """Validate style dict entries"""
    save_change = False
    for name, data in dict_user.items():
        # Reset invalid data set
        if not isinstance(data, dict):
            dict_user[name] = dict_def.copy()
            save_change = True
            continue
        # Reset invalid value or add missing
        for key, default_value in dict_def.items():
            if key not in data or not isinstance(
                data[key], type(default_value)
            ):
                data[key] = default_value
                save_change = True
    return save_change


class StyleValidator:
    """Style validator"""

    @staticmethod
    def classes(dict_user: dict[str, dict]) -> bool:
        """Classes style validator"""
        return validate_style(dict_user, CLASSINFO_DEFAULT)

    @staticmethod
    def brakes(dict_user: dict[str, dict]) -> bool:
        """Brakes style validator"""
        return validate_style(dict_user, BRAKEINFO_DEFAULT)

    @staticmethod
    def compounds(dict_user: dict[str, dict]) -> bool:
        """Compounds style validator"""
        return validate_style(dict_user, COMPOUNDINFO_DEFAULT)

    @staticmethod
    def tracks(dict_user: dict[str, dict]) -> bool:
        """Tracks style validator"""
        return validate_style(dict_user, TRACKINFO_DEFAULT)

    @staticmethod
    def filelock(dict_user: dict[str, dict]) -> bool:
        """File lock validator"""
        return validate_style(dict_user, FILELOCKINFO_DEFAULT)


class ValueValidator:
    """Value validator"""

    @staticmethod
    def boolean(key: str, dict_user: dict) -> bool:
        """Value - Boolean"""
        if not re.search(rxp.CFG_BOOL, key):
            return False
        if not isinstance(dict_user[key], bool):
            dict_user[key] = bool(dict_user[key])
        return True

    @staticmethod
    def choice_units(key: str, dict_user: dict) -> bool:
        """Value - units choice list"""
        for ref_key, choice_list in rxp.CHOICE_UNITS.items():
            if re.search(ref_key, key):
                if dict_user[key] not in choice_list:
                    dict_user.pop(key)
                return True
        return False

    @staticmethod
    def choice_common(key: str, dict_user: dict) -> bool:
        """Value - common choice list"""
        for ref_key, choice_list in rxp.CHOICE_COMMON.items():
            if re.search(ref_key, key):
                if dict_user[key] not in choice_list:
                    dict_user.pop(key)
                return True
        return False

    @staticmethod
    def color(key: str, dict_user: dict) -> bool:
        """Value - Color string"""
        if not re.search(rxp.CFG_COLOR, key):
            return False
        if not is_hex_color(dict_user[key]):
            dict_user.pop(key)
        return True

    @staticmethod
    def clock_format(key: str, dict_user: dict) -> bool:
        """Value - clock format string"""
        if not re.search(rxp.CFG_CLOCK_FORMAT, key):
            return False
        if not is_clock_format(dict_user[key]):
            dict_user.pop(key)
        return True

    @staticmethod
    def string(key: str, dict_user: dict) -> bool:
        """Value - string"""
        if not re.search(COMMON_STRINGS, key):
            return False
        if not isinstance(dict_user[key], str):
            dict_user.pop(key)
        return True

    @staticmethod
    def integer(key: str, dict_user: dict) -> bool:
        """Value - integer"""
        if not re.search(rxp.CFG_INTEGER, key):
            return False
        if not isinstance(dict_user[key], int) or isinstance(dict_user[key], bool):
            dict_user.pop(key)
        return True

    @staticmethod
    def numeric(key: str, dict_user: dict) -> bool:
        """Value - numeric"""
        if not isinstance(dict_user[key], (float, int)) or isinstance(dict_user[key], bool):
            dict_user.pop(key)
        return True


class PresetValidator:
    """Preset validator"""

    # Set validator methods in ordered list
    _value_validators = (
        ValueValidator.boolean,
        ValueValidator.choice_units,
        ValueValidator.choice_common,
        ValueValidator.color,
        ValueValidator.clock_format,
        ValueValidator.string,
        ValueValidator.integer,
        ValueValidator.numeric,
    )

    @classmethod
    def remove_invalid_key(cls, key_list_def: tuple[str, ...], dict_user: dict) -> None:
        """Remove invalid key & value from user dictionary"""
        key_list_user = tuple(dict_user)  # create user key list

        for key in key_list_user:  # loop through user key list
            # Remove invalid key
            if key not in key_list_def:  # check in default list
                dict_user.pop(key)
                continue
            # Skip sub_level dict
            if isinstance(dict_user[key], dict):
                continue
            # Validate values
            for _validator in cls._value_validators:
                if _validator(key, dict_user):
                    break

    @staticmethod
    def fix_outdated_key(dict_user: dict) -> None:
        """Fix outdated key name from user dictionary"""
        key_list_user = tuple(dict_user)  # create user key list
        # Rename key, remove outdated key
        for key in key_list_user:
            # Typo (<=2.33.0)
            if "predication" in key:
                dict_user[key.replace("predication", "prediction")] = dict_user.pop(key)
                continue

    @staticmethod
    def add_missing_key(key_list_def: tuple[str, ...], dict_user: dict, dict_def: dict) -> bool:
        """Add missing default key to user list"""
        is_modified = False
        key_list_user = tuple(dict_user)  # create user key list

        for key in key_list_def:  # loop through default key list
            if key not in key_list_user:  # check each default key in user list
                dict_user[key] = dict_def[key]  # add missing item to user
                is_modified = True

        return is_modified

    @staticmethod
    def sort_key_order(key_list_def: tuple[str, ...], dict_user: dict) -> None:
        """Sort user key order according to default key list"""
        for d_key in key_list_def:  # loop through default key list
            temp_value = dict_user[d_key]  # store user value
            dict_user.pop(d_key)  # delete user key
            dict_user[d_key] = temp_value  # append user key at the end

    @classmethod
    def validate_key_pair(cls, dict_user: dict, dict_def: dict, fix_key: bool) -> None:
        """Create key-only check list, then validate key"""
        key_list_def = tuple(dict_def)
        if fix_key:
            cls.fix_outdated_key(dict_user)
        cls.remove_invalid_key(key_list_def, dict_user)
        cls.add_missing_key(key_list_def, dict_user, dict_def)
        cls.sort_key_order(key_list_def, dict_user)

    @staticmethod
    def update_api_setting(dict_user: dict) -> None:
        """Update old API setting"""
        # (<=2.34.0)
        if "telemetry_api" not in dict_user:
            api_config = dict_user.get("shared_memory_api")
            if isinstance(api_config, dict):
                # Copy "shared_memory_api" to "telemetry_api"
                dict_user["telemetry_api"] = api_config.copy()
                api_config = dict_user["telemetry_api"]
                # Copy "module_restapi" setting to "telemetry_api"
                if "module_restapi" in dict_user:
                    restapi_old = dict_user["module_restapi"]
                    api_config["enable_restapi_access"] = restapi_old.get("enable", True)
                    api_config["restapi_update_interval"] = restapi_old.get("update_interval", 200)
                    api_config.update(restapi_old)

    @classmethod
    def validate(cls, dict_user: dict, dict_def: dict) -> dict:
        """Validate setting"""
        cls.update_api_setting(dict_user)
        # Check top-level key
        cls.validate_key_pair(dict_user, dict_def, False)
        # Check sub-level key
        for item in dict_user.keys():  # list each key lists
            cls.validate_key_pair(dict_user[item], dict_def[item], True)
        return dict_user
