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
File constants
"""


def qfile_filter(extension: str, description: str) -> str:
    """File format filter for QFile dialog

    Returns:
        "File description (*.extension)"
    """
    return f"{description} (*{extension})"


class ConfigType:
    """Configuration types"""

    # Global preset
    CONFIG = "config"
    FILELOCK = "filelock"
    SHORTCUTS = "shortcuts"
    # User preset
    SETTING = "setting"
    # Module ID
    MODULE = "module"
    WIDGET = "widget"
    # Style preset
    BRAKES = "brakes"
    BRANDS = "brands"
    CLASSES = "classes"
    COMPOUNDS = "compounds"
    HEATMAP = "heatmap"
    TRACKS = "tracks"


class FileExt:
    """File extension constants"""

    # Common
    ALL = ".*"
    LOG = ".log"
    CSV = ".csv"
    TXT = ".txt"
    INI = ".ini"
    BAK = ".bak"
    JSON = ".json"
    # Image
    SVG = ".svg"
    PNG = ".png"
    # Specific
    CONSUMPTION = ".consumption"
    ENERGY = ".energy"
    FUEL = ".fuel"
    SECTOR = ".sector"
    TPPN = ".tppn"
    TPTN = ".tptn"
    STATS = ".stats"
    LOCK = ".lock"


class FileFilter:
    """File filter constants (for used in QFileDialog)"""

    # Common
    ALL = qfile_filter(FileExt.ALL, "All files")
    LOG = qfile_filter(FileExt.LOG, "LOG file")
    TXT = qfile_filter(FileExt.TXT, "Text file")
    CSV = qfile_filter(FileExt.CSV, "CSV file")
    INI = qfile_filter(FileExt.INI, "INI file")
    JSON = qfile_filter(FileExt.JSON, "JSON file")
    # Image
    SVG = qfile_filter(FileExt.SVG, "SVG image")
    PNG = qfile_filter(FileExt.PNG, "PNG image")
    # Specific
    CONSUMPTION = qfile_filter(FileExt.CONSUMPTION, "Consumption History")
    TPPN = qfile_filter(FileExt.TPPN, "TinyPedal Pace Notes")
    TPTN = qfile_filter(FileExt.TPTN, "TinyPedal Track Notes")
    GPLINI = qfile_filter(FileExt.INI, "GPL Pace Notes")


class ImageFile:
    """Built-in image file constants"""

    APP_ICON = "images/icon.png"
    COMPASS = "images/icon_compass.png"
    INSTRUMENT = "images/icon_instrument.png"
    STEERING_WHEEL = "images/icon_steering_wheel.png"
    WEATHER = "images/icon_weather.png"


class StatsFile:
    """Stats file name constants"""

    DRIVER = "driver"


class LogFile:
    """Log file name constants"""

    APP_LOG = "tinypedal.log"
    PID = "pid.log"
