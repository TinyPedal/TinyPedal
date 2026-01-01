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
Brand logo file function
"""

import os

from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap

from ..const_file import FileExt


def exceeded_max_logo_width(
    org_width: int, org_height: int, max_width: int, max_height: int
) -> bool:
    """Whether exceeded max logo width"""
    return org_width * max_height / max(org_height, 1) > max_width


def load_brand_logo_file(
    filepath:str, filename: str, max_width: int, max_height: int, extension: str = FileExt.PNG
) -> QPixmap:
    """Load brand logo file (*.png)"""
    filename_full = f"{filepath}{filename}{extension}"
    # Check existing file and size < 1mb
    if not os.path.exists(filename_full) or os.path.getsize(filename_full) > 1024000:
        return QPixmap()
    # Load and scale logo
    logo = QPixmap(filename_full)
    if exceeded_max_logo_width(logo.width(), logo.height(), max_width, max_height):
        logo_scaled = logo.scaledToWidth(max_width, mode=Qt.SmoothTransformation)
    else:
        logo_scaled = logo.scaledToHeight(max_height, mode=Qt.SmoothTransformation)
    return logo_scaled
