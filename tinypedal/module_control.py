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
Module and widget control
"""

from __future__ import annotations

import logging
from time import sleep
from types import MappingProxyType
from typing import Any, KeysView

from . import module, widget
from .const_file import ConfigType
from .setting import cfg

logger = logging.getLogger(__name__)


def create_module_pack(target: Any) -> dict:
    """Create module reference pack as dictionary

    Args:
        target: module.

    Returns:
        Dictionary, key = module name. value = imported module.
    """
    return {name: getattr(target, name) for name in target.__all__}


class ModuleControl:
    """Module and widget control

    Args:
        target: module.

    Attributes:
        type_id: module type indentifier, either "module" or "widget".
        active_modules: active module reference dict (read-only).
    """

    __slots__ = (
        "_imported_modules",
        "_active_modules",
        "type_id",
        "active_modules",
    )

    def __init__(self, target: Any, type_id: str):
        self._imported_modules = create_module_pack(target)
        self._active_modules: dict = {}
        self.type_id = type_id
        self.active_modules: MappingProxyType = MappingProxyType(self._active_modules)

    def start(self, name: str = ""):
        """Start module, specify name for selected module"""
        if name:
            self.__start_selected(name)
        else:
            self.__start_enabled()

    def close(self, name: str = ""):
        """Close module, specify name for selected module"""
        if name:
            self.__close_selected(name)
        else:
            self.__close_enabled()

    def reload(self, name: str = ""):
        """Reload module"""
        self.close(name)
        self.start(name)

    def toggle(self, name: str):
        """Toggle module"""
        if cfg.user.setting[name]["enable"]:
            cfg.user.setting[name]["enable"] = False
            self.__close_selected(name)
        else:
            cfg.user.setting[name]["enable"] = True
            self.__start_selected(name)
        cfg.save()

    def enable_all(self):
        """Enable all modules"""
        for _name in self._imported_modules.keys():
            cfg.user.setting[_name]["enable"] = True
        self.start()
        cfg.save()
        logger.info("ENABLED: all %s(s)", self.type_id)

    def disable_all(self):
        """Disable all modules"""
        for _name in self._imported_modules.keys():
            cfg.user.setting[_name]["enable"] = False
        self.close()
        cfg.save()
        logger.info("DISABLED: all %s(s)", self.type_id)

    def __start_enabled(self):
        """Start all enabled module"""
        for _name in self._imported_modules.keys():
            self.__start_selected(_name)

    def __start_selected(self, name: str):
        """Start selected module"""
        if cfg.user.setting[name]["enable"] and name not in self._active_modules:
            # Create module instance and add to dict
            self._active_modules[name] = self._imported_modules[name].Realtime(cfg, name)
            self._active_modules[name].start()

    def __close_enabled(self):
        """Close all enabled module"""
        for _name in tuple(self._active_modules):
            self.__close_selected(_name)

    def __close_selected(self, name: str):
        """Close selected module"""
        if name in self._active_modules:
            _module = self._active_modules[name]  # get instance
            self._active_modules.pop(name)  # remove active reference
            _module.stop()  # close module
            while not _module.closed:  # wait finish
                sleep(0.01)
            _module = None  # remove final reference

    @property
    def number_active(self) -> int:
        """Number of active modules"""
        return len(self._active_modules)

    @property
    def number_total(self) -> int:
        """Number of total modules"""
        return len(self._imported_modules)

    @property
    def names(self) -> KeysView[str]:
        """List of module names"""
        return self._imported_modules.keys()


mctrl = ModuleControl(target=module, type_id=ConfigType.MODULE)
wctrl = ModuleControl(target=widget, type_id=ConfigType.WIDGET)
