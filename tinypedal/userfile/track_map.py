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
Track map file function
"""

from __future__ import annotations

import logging

from ..constant import DATA, FILE
from ..validator import image_exists, invalid_save_name

logger = logging.getLogger(__name__)


def string_pair_to_int(string: str) -> tuple[int, int]:
    """Convert string pair "x,y" to int list"""
    value = string.split(",")
    return int(value[0]), int(value[1])


def string_pair_to_float(string: str) -> tuple[float, float]:
    """Convert string pair "x,y" to float list"""
    value = string.split(",")
    return float(value[0]), float(value[1])


def list_pair_to_string(data: tuple | list, decimals: int = -1) -> str:
    """Convert list pair (x,y) to string pair"""
    if decimals >= 0:
        return f"{data[0]:.{decimals}f},{data[1]:.{decimals}f}"
    return f"{data[0]},{data[1]}"


def points_to_coords(points: str) -> tuple[tuple[float, float], ...]:
    """Convert svg points strings to raw coordinates

    Args:
        points: "x,y x,y ..." svg points strings.

    Returns:
        ((x,y), (x,y), ...) raw coordinates.
    """
    return tuple(string_pair_to_float(xy) for xy in points.split(" "))


def coords_to_points(coords: tuple | list, decimals: int = -1) -> str:
    """Convert raw coordinates to svg points strings

    Args:
        coords: ((x,y), (x,y), ...) raw coordinates.
        decimals: number of decimal points to keep, -1 = keeping all decimals.

    Returns:
        "x,y x,y ..." svg points strings.
    """
    return " ".join(list_pair_to_string(xy, decimals) for xy in coords)


def load_track_map_file(
    filepath: str, filename: str, extension: str = FILE.EXT_SVG
) -> tuple[tuple, ...]:
    """Load svg track map file (*.svg)"""
    full_filename = f"{filepath}{filename}{extension}"
    try:
        track_title = None
        track_sector = None
        track_map = None
        track_dist = None
        # Check existing file and size < 5MB
        if not image_exists(full_filename, extension, 5_120_000):
            raise ValueError
        # Parse track map data
        with open(full_filename, "r", encoding="utf-8") as svg_data:
            for line in svg_data:
                if not track_title:
                    temp_data = _read_data(line, "<title>", "</title>")
                    if temp_data:
                        track_title = temp_data
                    continue
                if not track_sector:
                    temp_data = _read_data(line, "<desc>", "</desc>")
                    if temp_data:
                        track_sector = temp_data
                    continue
                if not track_map:
                    temp_data = _read_data(line, '<polyline id="map"', '"/>', 'points="')
                    if temp_data:
                        track_map = temp_data
                    continue
                if not track_dist:
                    temp_data = _read_data(line, '<polyline id="dist"', '"/>', 'points="')
                    if temp_data:
                        track_dist = temp_data
                    continue
        # Convert to coordinates list
        raw_coords = points_to_coords(track_map)
        raw_dists = points_to_coords(track_dist)
        sector_index = string_pair_to_int(track_sector)
        return raw_coords, raw_dists, sector_index
    except FileNotFoundError:
        logger.info("MISSING: track map (%s) data", extension)
    except (AttributeError, IndexError, ValueError, TypeError):
        logger.info("MISSING: invalid track map (%s) data", extension)
    return (), (), ()


def save_track_map_file(
    filepath: str,
    filename: str,
    view_box: str,
    raw_coords: tuple,
    raw_dists: tuple,
    sector_index: tuple,
    decimals: int,
    extension: str = FILE.EXT_SVG,
) -> None:
    """Save track map file (*.svg)"""
    if invalid_save_name(filename):
        return
    # Convert to svg coordinates
    map_coords = coords_to_points(raw_coords, decimals)
    map_dists = coords_to_points(raw_dists, decimals)
    # Save svg
    full_filename = f"{filepath}{filename}{extension}"
    with open(full_filename, "w", encoding="utf-8", newline=DATA.CRLF) as svgfile:
        writer = svgfile.write
        # XML declaration
        writer('<?xml version="1.0" encoding="utf-8"?>\n')
        writer("<!-- Track map generated with TinyPedal -->\n")
        # SVG start tag
        writer(f'<svg viewBox="{view_box}" version="1.1" xmlns="http://www.w3.org/2000/svg">\n')
        # SVG title
        writer(f"\t<title>{filename}</title>\n")
        # SVG description (sector)
        writer("\t<!-- Sector coordinates index -->\n")
        writer(f"\t<desc>{sector_index[0]},{sector_index[1]}</desc>\n")
        # SVG map coordinates
        writer("\t<!-- Raw global coordinates -->\n")
        writer(f'\t<polyline id="map" fill="none" stroke="black" stroke-width="10" points="{map_coords}"/>\n')
        # SVG distance elevation coordinates
        writer("\t<!-- Raw distance reference points -->\n")
        writer(f'\t<polyline id="dist" fill="none" stroke="none" stroke-width="0" points="{map_dists}"/>\n')
        # SVG end tag
        writer("</svg>\n")
        logger.info("USERDATA: %s%s saved", filename, extension)


def _read_data(data: str, start: str, end: str, mid: str = "") -> str | None:
    """Read svg data"""
    pos_beg = data.find(start)
    if pos_beg < 0:
        return None
    if mid:
        start = mid
        pos_beg = data.find(start)
        if pos_beg < 0:
            return None
    pos_end = data.find(end)
    return data[pos_beg+len(start):pos_end]
