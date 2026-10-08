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

from collections import ChainMap
from types import MappingProxyType

from .. import paths
from ..constant import DATA, FILE
from ..decorator import slotclass


@slotclass
class FileName:
    """File name (with extension)"""

    # Global preset
    config: str = f"config{FILE.EXT_JSON}"
    filelock: str = f"config{FILE.EXT_LOCK}"
    shortcuts: str = f"shortcuts{FILE.EXT_JSON}"
    # User preset
    setting: str = f"default{FILE.EXT_JSON}"
    # Style preset
    brakes: str = f"brakes{FILE.EXT_JSON}"
    brands: str = f"brands{FILE.EXT_JSON}"
    classes: str = f"classes{FILE.EXT_JSON}"
    compounds: str = f"compounds{FILE.EXT_JSON}"
    heatmap: str = f"heatmap{FILE.EXT_JSON}"
    tracks: str = f"tracks{FILE.EXT_JSON}"


@slotclass
class FilePath:
    """File path"""

    # Global path, should not be modified
    config: str = ""
    # User setting path
    settings: str = ""
    # User data path
    brand_logo: str = ""
    delta_best: str = ""
    energy_delta: str = ""
    fuel_delta: str = ""
    pace_notes: str = ""
    sector_best: str = ""
    track_map: str = ""
    track_notes: str = ""
    car_setups: str = ""

    def update(self, user_path: dict, default_path: dict):
        """Update path variables from global user path dictionary"""
        for key, path in user_path.items():
            # Reset path if invalid
            if not paths.user_data_path(path):
                path = paths.user_data_path(default_path[key])
                user_path[key] = path
            # Assign path
            path_name = key.replace("_path", "")
            setattr(self, path_name, path)


@slotclass
class Setting:
    """Preset setting"""

    # Global preset
    config: dict = DATA.EMPTY_DICT
    filelock: dict = DATA.EMPTY_DICT
    shortcuts: dict = DATA.EMPTY_DICT
    # User preset
    setting: dict = DATA.EMPTY_DICT
    # Style preset
    brakes: dict = DATA.EMPTY_DICT
    brands: dict = DATA.EMPTY_DICT
    classes: dict = DATA.EMPTY_DICT
    compounds: dict = DATA.EMPTY_DICT
    heatmap: dict = DATA.EMPTY_DICT
    tracks: dict = DATA.EMPTY_DICT

    def set_default(self):
        """Set default setting (one time only)"""
        if self.config != DATA.EMPTY_DICT:
            return
        from .default_api import API_DEFAULT
        from .default_brakes import BRAKES_DEFAULT
        from .default_classes import CLASSES_DEFAULT
        from .default_common import COMMON_DEFAULT
        from .default_compounds import COMPOUNDS_DEFAULT
        from .default_filelock import FILELOCK_DEFAULT
        from .default_global import GLOBAL_DEFAULT
        from .default_heatmap import HEATMAP_DEFAULT
        from .default_module import MODULE_DEFAULT
        from .default_shortcuts import (
            SHORTCUTS_GENERAL,
            SHORTCUTS_MODULE,
            SHORTCUTS_PRESET,
            SHORTCUTS_WIDGET,
        )
        from .default_tracks import TRACKS_DEFAULT
        from .default_widget import WIDGET_DEFAULT

        self.config = MappingProxyType(GLOBAL_DEFAULT)
        self.filelock = MappingProxyType(FILELOCK_DEFAULT)
        self.shortcuts = MappingProxyType(ChainMap(SHORTCUTS_MODULE, SHORTCUTS_WIDGET, SHORTCUTS_PRESET, SHORTCUTS_GENERAL))
        self.setting = MappingProxyType(ChainMap(WIDGET_DEFAULT, MODULE_DEFAULT, API_DEFAULT, COMMON_DEFAULT))
        self.brakes = MappingProxyType(BRAKES_DEFAULT)
        self.brands = DATA.EMPTY_DICT
        self.classes = MappingProxyType(CLASSES_DEFAULT)
        self.compounds = MappingProxyType(COMPOUNDS_DEFAULT)
        self.heatmap = MappingProxyType(HEATMAP_DEFAULT)
        self.tracks = MappingProxyType(TRACKS_DEFAULT)
