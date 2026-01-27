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
User file access function
"""

import logging
import os

from ..const_app import APP_NAME, PLATFORM

logger = logging.getLogger(__name__)


def set_user_data_path(filepath: str) -> str:
    """Set user data path, create if not exist"""
    if not os.path.exists(filepath):
        logger.info("%s folder does not exist, attemp to create", filepath)
        try:
            os.mkdir(filepath)
        except (PermissionError, FileExistsError, FileNotFoundError):
            logger.error("failed to create %s folder", filepath)
            return ""
    return filepath


def set_relative_path(filepath: str) -> str:
    """Convert absolute path to relative if path is inside APP root folder"""
    try:
        rel_path = os.path.relpath(filepath)
        if rel_path.startswith(".."):
            output_path = filepath
        else:
            output_path = rel_path
    except ValueError:
        output_path = filepath
    # Convert backslash to slash
    output_path = output_path.replace("\\", "/")
    # Make sure path end with "/"
    if not output_path.endswith("/"):
        output_path += "/"
    return output_path


def set_global_config_path(filepath: str) -> str:
    """Set path for global configurable user files, create if not exist

    Default to APPDATA folder (AppData/Roaming) on Windows.
    Default to XDG_CONFIG_HOME ($HOME/.config) on Linux.
    """
    if PLATFORM == "Windows":
        return set_user_data_path(f"{os.getenv('APPDATA', '.')}\\{filepath}\\")
    # Linux
    from xdg import BaseDirectory as BD
    return BD.save_config_path(filepath) + "/"


def set_default_config_path(filepath: str) -> str:
    """Set path for default configurable user files

    Default to TinyPedal local folder (./) on Windows.
    Default to XDG_CONFIG_HOME ($HOME/.config) on Linux.
    """
    if PLATFORM == "Windows":
        return filepath
    # Linux
    from xdg import BaseDirectory as BD
    return BD.save_config_path(APP_NAME, filepath)


def set_default_data_path(filepath: str) -> str:
    """Set path for default non-configurable data files

    Default to TinyPedal local folder (./) on Windows.
    Default to XDG_DATA_HOME ($HOME/.local/share) on Linux.
    """
    if PLATFORM == "Windows":
        return filepath
    # Linux
    from xdg import BaseDirectory as BD
    return BD.save_data_path(APP_NAME, filepath)
