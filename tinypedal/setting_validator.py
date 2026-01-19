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
Setting validator function
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from . import regex_pattern as rxp
from . import version
from .const_common import VERSION_NA
from .setting_preupdate import preupdate_specific_version
from .template.setting_brakes import BRAKEINFO_DEFAULT
from .template.setting_classes import CLASSINFO_DEFAULT
from .template.setting_compounds import COMPOUNDINFO_DEFAULT
from .template.setting_filelock import FILELOCKINFO_DEFAULT
from .template.setting_heatmap import HEATMAP_DEFAULT
from .template.setting_tracks import TRACKINFO_DEFAULT
from .validator import is_clock_format, is_hex_color
from .version_check import parse_version_string


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
    def heatmap(dict_user: dict[str, dict]) -> bool:
        """Heatmap style validator"""
        save_change = PresetValidator.add_missing_key(dict_user, HEATMAP_DEFAULT)
        # Sort styles
        if save_change:
            # Place default keys in front
            key_list_def = list(HEATMAP_DEFAULT)
            # Append user keys
            for key in dict_user:
                if key not in HEATMAP_DEFAULT:
                    key_list_def.append(key)
            for d_key in key_list_def:
                dict_user[d_key] = dict_user.pop(d_key)  # append user key at the end
        return save_change

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
        for strings in (
            rxp.CFG_FONT_NAME,
            rxp.CFG_HEATMAP,
            rxp.CFG_USER_PATH,
            rxp.CFG_USER_IMAGE,
            rxp.CFG_STRING,
        ):
            if re.search(strings, key):
                break
        else:
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

    # Set validator methods in order
    _value_validators = tuple(
        getattr(ValueValidator, key)
        for key, value in ValueValidator.__dict__.items()
        if isinstance(value, staticmethod)
    )

    @classmethod
    def remove_invalid_key(cls, dict_user: dict, dict_def: dict) -> None:
        """Remove invalid key & value from user dictionary"""
        key_list_user = tuple(dict_user)  # create user key list

        for key in key_list_user:  # loop through user key list
            # Remove invalid key
            if key not in dict_def:  # check in default list
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
    def add_missing_key(dict_user: dict, dict_def: dict) -> bool:
        """Add missing default key to user list"""
        is_modified = False
        key_list_user = tuple(dict_user)  # create user key list

        for key in dict_def:  # loop through default keys
            if key not in key_list_user:  # check each default key in user list
                data_def = dict_def[key]
                # Add missing item to user
                if isinstance(data_def, dict):
                    dict_user[key] = data_def.copy()  # copy sub-dict
                else:
                    dict_user[key] = data_def
                is_modified = True

        return is_modified

    @staticmethod
    def sort_key_order(dict_user: dict, dict_def: dict) -> None:
        """Sort user key order according to default key list"""
        for d_key in dict_def:  # loop through default keys
            dict_user[d_key] = dict_user.pop(d_key)  # append user key at the end

    @classmethod
    def validate_key_pair(cls, dict_user: dict, dict_def: dict) -> None:
        """Create key-only check list, then validate key"""
        cls.remove_invalid_key(dict_user, dict_def)
        cls.add_missing_key(dict_user, dict_def)
        cls.sort_key_order(dict_user, dict_def)

    @staticmethod
    def preupdate_global_preset(dict_user: dict):
        """Pre update global preset, run before validation"""
        telemetry_api = dict_user.get("telemetry_api")
        if isinstance(telemetry_api, dict):
            dict_user["telemetry"] = telemetry_api.copy()

    @staticmethod
    def preupdate_user_preset(dict_user: dict, dict_def: dict):
        """Pre update user preset, run before validation"""
        # Check preset version
        preset_info = dict_user.get("preset")
        if not isinstance(preset_info, dict):
            dict_user["preset"] = {}
            preset_info = dict_user["preset"]
        preset_version = parse_version_string(preset_info.get("version", "0.0.0"))

        # Update preset version
        dict_user["preset"]["version"] = dict_def["preset"]["version"]

        # Skip check if already newest version
        build_version = parse_version_string(version.__version__)
        if preset_version == VERSION_NA or preset_version < build_version:
            preupdate_specific_version(preset_version, dict_user)

    @classmethod
    def global_preset(cls, dict_user: dict, dict_def: dict) -> dict:
        """Validate global preset"""
        cls.preupdate_global_preset(dict_user)
        return cls._validate(dict_user, dict_def)

    @classmethod
    def user_preset(cls, dict_user: dict, dict_def: dict) -> dict:
        """Validate user preset"""
        cls.preupdate_user_preset(dict_user, dict_def)
        return cls._validate(dict_user, dict_def)

    @classmethod
    def _validate(cls, dict_user: dict, dict_def: dict) -> dict:
        """Validate setting"""
        # Check top-level key
        cls.validate_key_pair(dict_user, dict_def)
        # Check sub-level key
        for item in dict_user:
            cls.validate_key_pair(dict_user[item], dict_def[item])
        return dict_user
