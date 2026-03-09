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
Custom image file function
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter, QPixmap

from ..const_file import FileExt
from ..validator import image_exists


def split_pixmap_image(
    image: QPixmap, size: int, h_offset: int = 0, v_offset: int = 0
) -> QPixmap:
    """Split pixmap icon set"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.drawPixmap(0, 0, image, size * h_offset, size * v_offset, 0, 0)
    return pixmap


def exceeded_max_logo_width(
    org_width: int, org_height: int, max_width: int, max_height: int
) -> bool:
    """Whether exceeded max logo width"""
    return org_width * max_height / max(org_height, 1) > max_width


def load_brand_logo_image(
    filepath:str, filename: str, max_width: int, max_height: int, extension: str = FileExt.PNG
) -> QPixmap:
    """Load brand logo image (*.png)"""
    filename_full = f"{filepath}{filename}{extension}"
    # Check existing file and size < 5MB
    if not image_exists(filename_full, extension, 5_120_000):
        return QPixmap()
    # Load and scale logo
    image = QPixmap(filename_full)
    if exceeded_max_logo_width(image.width(), image.height(), max_width, max_height):
        logo_scaled = image.scaledToWidth(max_width, mode=Qt.SmoothTransformation)
    else:
        logo_scaled = image.scaledToHeight(max_height, mode=Qt.SmoothTransformation)
    return logo_scaled


def load_custom_image(
    user_file: str, default_file: str, width: int = 0, height: int = 0, extension: str = FileExt.PNG
) -> QPixmap:
    """Load custom image (*.png)

    Scale to width if only width set;
    Scale to height if only height set;
    Scale to both if both set;
    """
    filename = default_file
    if user_file and image_exists(user_file, extension):
        filename = user_file
    image = QPixmap(filename)
    if width > 0 and height <= 0:
        return image.scaledToWidth(width, mode=Qt.SmoothTransformation)
    if height > 0 and width <= 0:
        return image.scaledToHeight(height, mode=Qt.SmoothTransformation)
    return image.scaled(width, height, mode=Qt.SmoothTransformation)
