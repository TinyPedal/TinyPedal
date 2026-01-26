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
Setting
"""

from __future__ import annotations

import logging
import os
import threading
from collections import ChainMap
from time import sleep
from types import MappingProxyType
from typing import Any

from .const_api import API_MAP_CONFIG
from .const_app import APP_NAME
from .const_common import EMPTY_DICT
from .const_file import ConfigType, FileExt
from .setting_validator import PresetValidator, StyleValidator
from .template.setting_api import API_DEFAULT
from .template.setting_brakes import BRAKES_DEFAULT
from .template.setting_classes import CLASSES_DEFAULT
from .template.setting_common import COMMON_DEFAULT
from .template.setting_compounds import COMPOUNDS_DEFAULT
from .template.setting_filelock import FILELOCK_DEFAULT
from .template.setting_global import GLOBAL_DEFAULT
from .template.setting_heatmap import HEATMAP_DEFAULT
from .template.setting_module import MODULE_DEFAULT
from .template.setting_shortcuts import SHORTCUTS_DEFAULT
from .template.setting_tracks import TRACKS_DEFAULT
from .template.setting_widget import WIDGET_DEFAULT
from .userfile import set_global_config_path, set_user_data_path
from .userfile.json_setting import (
    copy_setting,
    load_setting_json_file,
    load_style_json_file,
    save_and_verify_json_file,
)
from .validator import is_allowed_filename

logger = logging.getLogger(__name__)


class FileName:
    """File name"""

    __slots__ = (
        "config",
        "filelock",
        "shortcuts",
        "setting",
        "brakes",
        "brands",
        "classes",
        "compounds",
        "heatmap",
        "tracks",
    )

    def __init__(self):
        # Global preset
        self.config = f"config{FileExt.JSON}"
        self.filelock = f"config{FileExt.LOCK}"
        self.shortcuts = f"shortcuts{FileExt.JSON}"
        # User preset
        self.setting = f"default{FileExt.JSON}"
        # Style preset
        self.brakes = f"brakes{FileExt.JSON}"
        self.brands = f"brands{FileExt.JSON}"
        self.classes = f"classes{FileExt.JSON}"
        self.compounds = f"compounds{FileExt.JSON}"
        self.heatmap = f"heatmap{FileExt.JSON}"
        self.tracks = f"tracks{FileExt.JSON}"


class FilePath:
    """File path"""

    __slots__ = (
        "config",
        "settings",
        "brand_logo",
        "delta_best",
        "energy_delta",
        "fuel_delta",
        "pace_notes",
        "sector_best",
        "track_map",
        "track_notes",
    )

    def __init__(self):
        # Global path, should not be modified
        self.config = set_global_config_path(APP_NAME)
        # User setting path
        self.settings = ""
        # User data path
        self.brand_logo = ""
        self.delta_best = ""
        self.energy_delta = ""
        self.fuel_delta = ""
        self.pace_notes = ""
        self.sector_best = ""
        self.track_map = ""
        self.track_notes = ""

    def update(self, user_path: dict, default_path: dict):
        """Update path variables from global user path dictionary"""
        for key in user_path:
            # Reset path if invalid
            if not set_user_data_path(user_path[key]):
                user_path[key] = default_path[key]
                set_user_data_path(user_path[key])
            # Assign path
            setattr(self, key.replace("_path", ""), user_path[key])


class Preset:
    """Preset setting"""

    __slots__ = (
        "config",
        "filelock",
        "shortcuts",
        "setting",
        "brakes",
        "brands",
        "classes",
        "compounds",
        "heatmap",
        "tracks",
    )

    def __init__(self, default: bool = False):
        if not default:
            return
        # Global preset
        self.config = MappingProxyType(GLOBAL_DEFAULT)
        self.filelock = MappingProxyType(FILELOCK_DEFAULT)
        self.shortcuts = MappingProxyType(SHORTCUTS_DEFAULT)
        # User preset
        self.setting = MappingProxyType(ChainMap(WIDGET_DEFAULT, MODULE_DEFAULT, API_DEFAULT, COMMON_DEFAULT))
        # Style preset
        self.brakes = MappingProxyType(BRAKES_DEFAULT)
        self.brands = EMPTY_DICT
        self.classes = MappingProxyType(CLASSES_DEFAULT)
        self.compounds = MappingProxyType(COMPOUNDS_DEFAULT)
        self.heatmap = MappingProxyType(HEATMAP_DEFAULT)
        self.tracks = MappingProxyType(TRACKS_DEFAULT)


class Setting:
    """APP setting"""

    __slots__ = (
        "_save_delay",
        "_save_queue",
        "_setting_to_load",
        "is_saving",
        "version_update",
        "filename",
        "default",
        "user",
        "path",
    )

    def __init__(self):
        # States
        self._save_delay = 0
        self._save_queue = {}
        self._setting_to_load = ""
        self.is_saving = False
        self.version_update = 0
        # Settings
        self.filename = FileName()
        self.default = Preset(default=True)
        self.user = Preset()
        self.path = FilePath()

    @property
    def api(self) -> dict[str, Any]:
        """API setting (quick reference)"""
        return self.user.setting[self.api_key]

    @property
    def application(self) -> dict[str, Any]:
        """Application (global) setting (quick reference)"""
        return self.user.config["application"]

    @property
    def compatibility(self) -> dict[str, Any]:
        """Compatibility (global) setting (quick reference)"""
        return self.user.config["compatibility"]

    @property
    def notification(self) -> dict[str, Any]:
        """Notification (global) setting (quick reference)"""
        return self.user.config["notification"]

    @property
    def overlay(self) -> dict[str, Any]:
        """Overlay setting (quick reference)"""
        return self.user.setting["overlay"]

    @property
    def telemetry(self) -> dict[str, Any]:
        """Telemetry (global) setting (quick reference)"""
        return self.user.config["telemetry"]

    @property
    def units(self) -> dict[str, Any]:
        """Units setting (quick reference)"""
        return self.user.setting["units"]

    def is_loaded(self, filename: str) -> bool:
        """Check if selected setting file is already loaded"""
        return self.filename.setting == filename

    def set_next_to_load(self, filename: str):
        """Set next setting filename to load"""
        self._setting_to_load = filename

    def get_primary_preset_name(self, preset_name: str) -> str:
        """Get primary preset name and verify"""
        if is_allowed_filename(preset_name):
            full_preset_name = f"{preset_name}{FileExt.JSON}"
            if os.path.exists(f"{self.path.settings}{full_preset_name}"):
                return full_preset_name
        return ""

    def load_global(self):
        """Load global setting, should only done once per launch"""
        self.user.config = load_setting_json_file(
            filename=self.filename.config,
            filepath=self.path.config,
            dict_def=self.default.config,
            file_info="global preset",
            validator=PresetValidator.global_preset,
        )
        self.user.shortcuts = load_setting_json_file(
            filename=self.filename.shortcuts,
            filepath=self.path.config,
            dict_def=self.default.shortcuts,
            file_info="keyboard shortcuts",
            validator=PresetValidator.shortcuts_preset,
        )
        self.user.filelock = load_style_json_file(
            filename=self.filename.filelock,
            filepath=self.path.config,
            dict_def=self.default.filelock,
            file_info="file lock",
            validator=StyleValidator.filelock,
        )
        # Assign global path
        self.path.update(
            user_path=self.user.config["user_path"],
            default_path=self.default.config["user_path"],
        )

    def update_path(self):
        """Update global path, call this if "user_path" changed"""
        old_settings_path = os.path.abspath(self.path.settings)
        self.path.update(
            user_path=self.user.config["user_path"],
            default_path=self.default.config["user_path"],
        )
        new_settings_path = os.path.abspath(self.path.settings)
        # Update preset name if settings path changed
        if new_settings_path != old_settings_path:
            self.set_next_to_load(f"{self.preset_files()[0]}{FileExt.JSON}")

    def load_user(self):
        """Load user settings, should be called after loaded global setting"""
        # Load preset JSON file
        if self._setting_to_load != "":
            filename_setting_temp = self._setting_to_load
            self._setting_to_load = ""
        else:
            filename_setting_temp = self.filename.setting
        self.user.setting = load_setting_json_file(
            filename=filename_setting_temp,
            filepath=self.path.settings,
            dict_def=self.default.setting,
        )
        self.filename.setting = filename_setting_temp
        # Load style JSON file
        self.user.brakes = load_style_json_file(
            filename=self.filename.brakes,
            filepath=self.path.settings,
            dict_def=self.default.brakes,
            validator=StyleValidator.brakes,
        )
        self.user.brands = load_style_json_file(
            filename=self.filename.brands,
            filepath=self.path.settings,
            dict_def=self.default.brands,
        )
        self.user.classes = load_style_json_file(
            filename=self.filename.classes,
            filepath=self.path.settings,
            dict_def=self.default.classes,
            validator=StyleValidator.classes,
        )
        self.user.compounds = load_style_json_file(
            filename=self.filename.compounds,
            filepath=self.path.settings,
            dict_def=self.default.compounds,
            validator=StyleValidator.compounds,
        )
        self.user.heatmap = load_style_json_file(
            filename=self.filename.heatmap,
            filepath=self.path.settings,
            dict_def=self.default.heatmap,
            validator=StyleValidator.heatmap,
        )
        self.user.tracks = load_style_json_file(
            filename=self.filename.tracks,
            filepath=self.path.settings,
            dict_def=self.default.tracks,
            validator=StyleValidator.tracks,
        )

    @property
    def api_name(self) -> str:
        """Get selected api name"""
        if self.telemetry["enable_api_selection_from_preset"]:
            return self.user.setting["preset"]["api_name"]
        return self.telemetry["api_name"]

    @api_name.setter
    def api_name(self, name: str) -> None:
        """Set selected api name"""
        if self.telemetry["enable_api_selection_from_preset"]:
            self.user.setting["preset"]["api_name"] = name
        else:
            self.telemetry["api_name"] = name

    @property
    def api_key(self) -> str:
        """Get selected api config key name"""
        return API_MAP_CONFIG[self.api_name]

    def preset_files(self, by_date: bool = True, reverse: bool = True) -> list[str]:
        """Get user preset JSON filename list

        Arguments:
            by_date: whether sort by modified date or file name.
            reverse: reverse sort.

        Returns:
            JSON filename (without file extension) list.
        """
        if by_date:
            date_cfg_list = (
                (os.path.getmtime(f"{self.path.settings}{_filename}"), _filename[:-5])
                for _filename in os.listdir(self.path.settings)
                if _filename.lower().endswith(FileExt.JSON)
            )
            valid_cfg_list = [
                _filename[1]
                for _filename in sorted(date_cfg_list, reverse=reverse)
                if is_allowed_filename(_filename[1])
            ]
        else:
            name_cfg_list = (
                _filename[:-5]
                for _filename in os.listdir(self.path.settings)
                if _filename.lower().endswith(FileExt.JSON)
            )
            valid_cfg_list = [
                _filename
                for _filename in sorted(name_cfg_list, key=lambda n:n.lower(), reverse=reverse)
                if is_allowed_filename(_filename)
            ]
        if valid_cfg_list:
            return valid_cfg_list
        return ["default"]

    def create(self, filename: str):
        """Create default setting"""
        save_and_verify_json_file(
            dict_user=copy_setting(self.default.setting),
            filename=filename,
            filepath=self.path.settings,
            max_attempts=self.max_saving_attempts,
        )

    def save(self, delay: int = 66, cfg_type: str = ConfigType.SETTING, next_task: bool = False):
        """Save trigger, limit to one save operation for a given period.

        Args:
            count:
                Set time delay(count) that can be refreshed before starting saving thread.
                Default is roughly one sec delay, use 0 for instant saving.
            cfg_type:
                Set saving config type.
            next_task:
                Skip adding save task, run next save task in queue.
        """
        if not next_task:
            filename = getattr(self.filename, cfg_type, None)
            # Check if valid file name
            if filename is None:
                logger.error("USERDATA: invalid config type %s, abort saving", cfg_type)
            # Check if file is locked
            elif filename in self.user.filelock:
                logger.info("USERDATA: %s is locked, changes not saved", filename)
            # Add to save queue
            elif filename not in self._save_queue:
                # Save to global config path
                if cfg_type in (
                    ConfigType.CONFIG,
                    ConfigType.FILELOCK,
                    ConfigType.SHORTCUTS,
                ):
                    filepath = self.path.config
                # Save to settings (preset) path
                else:
                    filepath = self.path.settings
                dict_user = getattr(self.user, cfg_type)
                self._save_queue[filename] = (filepath, dict_user)

        for queue_filename, queue_filedata in self._save_queue.items():
            break  # get next file in queue
        else:
            return

        self._save_delay = delay

        if not self.is_saving:
            self.is_saving = True
            threading.Thread(
                target=self.__saving,
                args=(queue_filename, *queue_filedata),
            ).start()

    def __saving(self, filename: str, filepath: str, dict_user: dict):
        """Saving thread"""
        # Update save delay
        while self._save_delay > 0:
            self._save_delay -= 1
            sleep(0.01)

        save_and_verify_json_file(
            dict_user=dict_user,
            filename=filename,
            filepath=filepath,
            max_attempts=self.max_saving_attempts,
        )

        self._save_queue.pop(filename, None)
        self.is_saving = False
        self.version_update += 1

        # Run next save task in save queue if any
        if self._save_queue:
            self.save(0, next_task=True)

    @property
    def max_saving_attempts(self) -> int:
        """Get max saving attempts"""
        return max(self.application["maximum_saving_attempts"], 3)


# Assign config setting
cfg = Setting()
