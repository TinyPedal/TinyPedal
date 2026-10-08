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
Configuration
"""

from __future__ import annotations

import logging
import os
import threading
from time import sleep
from typing import Any

from .constant import API, CONFIG, FILE
from .setting import FileName, FilePath, Setting
from .setting.validator import PresetValidator, StyleValidator
from .userfile.json_setting import (
    load_setting_json_file,
    load_style_json_file,
    save_and_verify_json_file,
)
from .validator import is_allowed_filename

logger = logging.getLogger(__name__)


class Configuration:
    """Configure file, path, preset

    Attributes:
        default: Default setting.
        user: Current user setting.
        filename: User setting file name.
        path: User setting file path.
        version: Last updated (increment) version number.
    """

    __slots__ = (
        "_is_saving",
        "_save_delay",
        "_save_queue",
        "_setting_to_load",
        "default",
        "filename",
        "path",
        "user",
        "version",
    )

    def __init__(self):
        # States
        self._is_saving = False
        self._save_delay = 0
        self._save_queue = {}
        self._setting_to_load = ""
        # Settings
        self.default = Setting()
        self.filename = FileName()
        self.path = FilePath()
        self.user = Setting()
        self.version = 0

    @property
    def api(self) -> dict[str, Any]:
        """API setting (quick reference)"""
        return self.user.setting[API.MAP_CONFIG[self.selected_api]]

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

    @property
    def selected_api(self) -> str:
        """Get selected api name"""
        if self.telemetry["enable_api_selection_from_preset"]:
            return self.user.setting["preset"]["api_name"]
        return self.telemetry["api_name"]

    @selected_api.setter
    def selected_api(self, name: str) -> None:
        """Set selected api name"""
        if self.telemetry["enable_api_selection_from_preset"]:
            self.user.setting["preset"]["api_name"] = name
        else:
            self.telemetry["api_name"] = name

    @property
    def max_saving_attempts(self) -> int:
        """Get max saving attempts"""
        return max(self.application["maximum_saving_attempts"], 3)

    @property
    def max_loading_attempts(self) -> int:
        """Get max loading attempts"""
        return max(self.application["maximum_loading_attempts"], 1)

    @property
    def is_saving(self) -> bool:
        return self._is_saving

    def is_loaded(self, filename: str) -> bool:
        """Check if selected setting file is already loaded"""
        return self.filename.setting == filename

    def set_next_to_load(self, filename: str):
        """Set next setting filename to load"""
        self._setting_to_load = filename

    def get_primary_preset_name(self, preset_name: str) -> str:
        """Get primary preset name and verify"""
        if is_allowed_filename(preset_name):
            full_preset_name = f"{preset_name}{FILE.EXT_JSON}"
            if os.path.exists(f"{self.path.settings}{full_preset_name}"):
                return full_preset_name
        return ""

    def load_global(self):
        """Load global setting, should only done once per launch"""
        # Delayed init
        self.default.set_default()
        # Load setting
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
            self.set_next_to_load(f"{self.preset_files()[0]}{FILE.EXT_JSON}")

    def load_user(self):
        """Load user settings, should be called after loaded global setting"""
        loading_attempts = self.max_loading_attempts
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
            validator=PresetValidator.user_preset,
            max_attempts=loading_attempts,
        )
        self.filename.setting = filename_setting_temp
        # Load style JSON file
        self.user.brakes = load_style_json_file(
            filename=self.filename.brakes,
            filepath=self.path.settings,
            dict_def=self.default.brakes,
            validator=StyleValidator.brakes,
            max_attempts=loading_attempts,
        )
        self.user.brands = load_style_json_file(
            filename=self.filename.brands,
            filepath=self.path.settings,
            dict_def=self.default.brands,
            max_attempts=loading_attempts,
        )
        self.user.classes = load_style_json_file(
            filename=self.filename.classes,
            filepath=self.path.settings,
            dict_def=self.default.classes,
            validator=StyleValidator.classes,
            max_attempts=loading_attempts,
        )
        self.user.compounds = load_style_json_file(
            filename=self.filename.compounds,
            filepath=self.path.settings,
            dict_def=self.default.compounds,
            validator=StyleValidator.compounds,
            max_attempts=loading_attempts,
        )
        self.user.heatmap = load_style_json_file(
            filename=self.filename.heatmap,
            filepath=self.path.settings,
            dict_def=self.default.heatmap,
            validator=StyleValidator.heatmap,
            max_attempts=loading_attempts,
        )
        self.user.tracks = load_style_json_file(
            filename=self.filename.tracks,
            filepath=self.path.settings,
            dict_def=self.default.tracks,
            validator=StyleValidator.tracks,
            max_attempts=loading_attempts,
        )

    def preset_files(self, by_date: bool = True, reverse: bool = True) -> list[str]:
        """Get user preset JSON filename list

        Arguments:
            by_date: whether sort by modified date or file name.
            reverse: reverse sort.

        Returns:
            JSON filename (without file extension) list.
        """
        if by_date:
            date_file_list = (
                (os.path.getmtime(f"{self.path.settings}{_filename}"), _filename[:-5])
                for _filename in os.listdir(self.path.settings)
                if _filename.lower().endswith(FILE.EXT_JSON)
            )
            valid_file_list = [
                _filename[1]
                for _filename in sorted(date_file_list, reverse=reverse)
                if is_allowed_filename(_filename[1])
            ]
        else:
            name_file_list = (
                _filename[:-5]
                for _filename in os.listdir(self.path.settings)
                if _filename.lower().endswith(FILE.EXT_JSON)
            )
            valid_file_list = [
                _filename
                for _filename in sorted(name_file_list, key=lambda n:n.lower(), reverse=reverse)
                if is_allowed_filename(_filename)
            ]
        if valid_file_list:
            return valid_file_list
        return ["default"]

    def backup_files(self, filepath: str, extension: str = FILE.EXT_BACKUP) -> list[str]:
        """Get backup filename list

        Arguments:
            filepath: folder to search backup file.
            extension: file extension for partial matching backup file.

        Returns:
            Backup filename list.
        """
        date_file_list = (
            (os.path.getmtime(f"{filepath}{_filename}"), _filename)
            for _filename in os.listdir(filepath)
            if extension in _filename.lower()
        )
        valid_file_list = [
            _filename[1]
            for _filename in sorted(date_file_list, reverse=True)
        ]
        if valid_file_list:
            return valid_file_list
        return []

    def create(self, filename: str):
        """Create default setting"""
        save_and_verify_json_file(
            dict_user=dict(self.default.setting),
            filename=filename,
            filepath=self.path.settings,
            max_attempts=self.max_saving_attempts,
        )

    def save(self, delay: int = 66, config_type: str = CONFIG.TYPE_SETTING, next_task: bool = False):
        """Save trigger, limit to one save operation for a given period.

        Args:
            count:
                Set time delay(count) that can be refreshed before starting saving thread.
                Default is roughly one sec delay, use 0 for instant saving.
            config_type:
                Set saving config type.
            next_task:
                Skip adding save task, run next save task in queue.
        """
        if next_task:
            self._save_delay = 0
            return

        self._save_delay = delay
        filename = getattr(self.filename, config_type, None)
        if filename in self._save_queue:
            return

        # Check if valid file name
        if filename is None:
            logger.error("USERDATA: invalid config type %s, abort saving", config_type)
        # Check if file is locked
        elif filename in self.user.filelock:
            logger.info("USERDATA: %s is locked, changes not saved", filename)
        # Add to save queue
        elif filename not in self._save_queue:
            # Save to global config path
            if config_type in (
                CONFIG.TYPE_CONFIG,
                CONFIG.TYPE_FILELOCK,
                CONFIG.TYPE_SHORTCUTS,
            ):
                filepath = self.path.config
            # Save to settings (preset) path
            else:
                filepath = self.path.settings
            dict_user = getattr(self.user, config_type)
            self._save_queue[filename] = (filepath, dict_user)

        if not self._save_queue:
            return

        if not self._is_saving:
            self._is_saving = True
            threading.Thread(target=self.__saving).start()

    def __saving(self):
        """Saving thread"""
        # Update save delay
        while self._save_delay > 0:
            self._save_delay -= 1
            sleep(0.01)

        # Run next save task until queue empty
        saving_attempts = self.max_saving_attempts
        while self._save_queue:
            for filename, (filepath, dict_user) in self._save_queue.items():
                break  # get next file in queue

            save_and_verify_json_file(
                dict_user=dict_user,
                filename=filename,
                filepath=filepath,
                max_attempts=saving_attempts,
            )
            self._save_queue.pop(filename, None)

        self._is_saving = False
        self.version += 1
