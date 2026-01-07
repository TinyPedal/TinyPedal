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


def set_global_user_path(filepath: str, platform: str) -> str:
    """Set global user data path, create if not exist"""
    if platform == "Windows":
        path = set_user_data_path(f"{os.getenv('APPDATA', '.')}\\{filepath}\\")
    else:
        from xdg import BaseDirectory as BD

        path = BD.save_config_path(filepath) + "/"
    return path


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
