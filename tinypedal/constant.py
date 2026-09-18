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
Constants
"""

import platform
from types import MappingProxyType

from .decorator import constantclass

# Function

def version_format() -> str:
    """Format version"""
    from . import version
    ver_number = (version.__version__, version.DEVELOPMENT)
    return "-".join(ver for ver in ver_number if ver != "")


def qfile_filter(extension: str, description: str) -> str:
    """File format filter for QFile dialog

    Returns:
        "File description (*.extension)"
    """
    return f"{description} (*{extension})"


# Contants

@constantclass
class PLATFORM:
    """Platform constants"""

    # System info
    SYSTEM = platform.system()
    WINDOWS = bool(SYSTEM == "Windows")


@constantclass
class APP:
    """APP constants"""

    # Version
    VERSION = version_format()

    # Info
    TINYPEDAL = "TinyPedal"
    REPOSITORY = "TinyPedal/TinyPedal"
    COPYRIGHT = "Copyright (C) 2022-2026 TinyPedal developers"
    DESCRIPTION = "Free and Open Source telemetry overlay application for racing simulation."
    LICENSE = "Licensed under the GNU General Public License v3.0 or later."

    # URL
    URL_WEBSITE = f"https://github.com/{REPOSITORY}"
    URL_SOURCECODE = f"{URL_WEBSITE}/blob/master/"
    URL_USER_GUIDE = f"{URL_WEBSITE}/wiki/User-Guide"
    URL_FAQ = f"{URL_WEBSITE}/wiki/Frequently-Asked-Questions"
    URL_RELEASE = f"{URL_WEBSITE}/releases"


@constantclass
class API:
    """API constants"""

    # Name
    NAME_LMU = "Le Mans Ultimate"
    NAME_LMULEGACY = "Le Mans Ultimate (legacy)"
    NAME_RF2 = "rFactor 2"

    # Alias
    ALIAS_LMU = "LMU"
    ALIAS_LMULEGACY = "LMU*"
    ALIAS_RF2 = "RF2"

    # Config name
    CONFIG_LMU = "api_lmu"
    CONFIG_LMULEGACY = "api_lmu"
    CONFIG_RF2 = "api_rf2"

    # Mapping
    MAP_ALIAS = MappingProxyType({
        NAME_LMU: ALIAS_LMU,
        NAME_LMULEGACY: ALIAS_LMULEGACY,
        NAME_RF2: ALIAS_RF2,
    })
    MAP_CONFIG = MappingProxyType({
        NAME_LMU: CONFIG_LMU,
        NAME_LMULEGACY: CONFIG_LMULEGACY,
        NAME_RF2: CONFIG_RF2,
    })


@constantclass
class CONFIG:
    """Config constants"""

    # Configuration types
    # Global preset
    TYPE_CONFIG = "config"
    TYPE_FILELOCK = "filelock"
    TYPE_SHORTCUTS = "shortcuts"
    # User preset
    TYPE_SETTING = "setting"
    # Module ID
    TYPE_MODULE = "module"
    TYPE_WIDGET = "widget"
    # Style preset
    TYPE_BRAKES = "brakes"
    TYPE_BRANDS = "brands"
    TYPE_CLASSES = "classes"
    TYPE_COMPOUNDS = "compounds"
    TYPE_HEATMAP = "heatmap"
    TYPE_TRACKS = "tracks"


@constantclass
class DATA:
    """Data constants"""

    # Numeric
    FLOAT_INF = float("inf")
    MAX_VEHICLES = 128  # set vehicle data size limit
    MAX_SECONDS = 99999.0  # for lap or sector time limit
    MAX_METERS = 999999.0  # for distance limit
    MAX_LAPS = 2_147_483_647  # max laps

    MAX_FORECASTS = 5  # for weather forecast
    MAX_FORECAST_MINUTES = 9999.0  # for weather forecast
    ABS_ZERO_CELSIUS = -273.15  # absolute zero celsius

    # Text
    TEXT_PLACEHOLDER = "-"
    TEXT_NA = "n/a"
    TEXT_NOTAVAILABLE = "NOT AVAILABLE"
    TEXT_NOLAPTIME = "-:--.---"
    CRLF = "\r\n"

    # Data set
    EMPTY_DICT: MappingProxyType = MappingProxyType({})
    DELTA_ZERO = (0.0, 0.0)  # pos, target
    DELTA_DEFAULT = (DELTA_ZERO,)
    WHEELS_ZERO = (0.0, 0.0, 0.0, 0.0)  # FL, FR, RL, RR
    WHEELS_NA = (-1.0, -1.0, -1.0, -1.0)  # FL, FR, RL, RR
    WHEELS_DELTA_DEFAULT = (0.0, *WHEELS_ZERO)  # pos, target set
    RELATIVE_NA = (0.0, -1)  # relative time gap, player index
    VERSION_NA = (0, 0, 0)  # major, minor, patch
    DATE_NA = (0, 0, 0)  # year, month, day

    # ID selector
    TREND_SIGN = (
        "●",  # 0 = constant
        "▲",  # 1 = increasing
        "▼",  # -1 = decreasing
    )
    TYPE_ENERGY = (
        "FUEL",  # fuel
        "NRG",  # virtual energy
    )
    TYPE_RACELENGTH = (
        "TIME",  # time-based race length
        "LAPS",  # laps-based race length
    )
    SECTOR_ABBR_ID = ("S1", "S2", "S3")  # sector abbreviation
    PREV_SECTOR_INDEX = (2, 0, 1)  # select previous sector index with current index
    GEAR_SEQUENCE = {  # max 9 in RF2
        -1: "R",
        0: "N",
        1: "1",
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
    }.get
    COMPASS_BEARINGS = (
        (0, "N"),
        (22.5, "NE"),
        (67.5, "E"),
        (112.5, "SE"),
        (157.5, "S"),
        (202.5, "SW"),
        (247.5, "W"),
        (292.5, "NW"),
        (337.5, "N"),
    )


@constantclass
class FILE:
    """File constants"""

    # File path
    PATH_IMAGE = "images/"
    PATH_DOC = "docs/"
    PATH_THIRDPARTYLICENSES = "docs/licenses/"

    # File extension
    # Common
    EXT_ALL = ".*"
    EXT_LOG = ".log"
    EXT_CSV = ".csv"
    EXT_TXT = ".txt"
    EXT_INI = ".ini"
    EXT_BACKUP = ".backup"
    EXT_SVM = ".svm"
    EXT_JSON = ".json"
    # Image
    EXT_SVG = ".svg"
    EXT_PNG = ".png"
    EXT_ICO = ".ico"
    # Specific
    EXT_CONSUMPTION = ".consumption"
    EXT_ENERGY = ".energy"
    EXT_FUEL = ".fuel"
    EXT_SECTOR = ".sector"
    EXT_TPPN = ".tppn"
    EXT_TPTN = ".tptn"
    EXT_STATS = ".stats"
    EXT_LOCK = ".lock"
    EXT_TYRESTRATEGY = ".tyre-strategy"

    # File filter (for used in QFileDialog)
    # Common
    FILTER_ALL = qfile_filter(EXT_ALL, "All files")
    FILTER_LOG = qfile_filter(EXT_LOG, "LOG file")
    FILTER_TXT = qfile_filter(EXT_TXT, "Text file")
    FILTER_CSV = qfile_filter(EXT_CSV, "CSV file")
    FILTER_INI = qfile_filter(EXT_INI, "INI file")
    FILTER_JSON = qfile_filter(EXT_JSON, "JSON file")
    # Image
    FILTER_SVG = qfile_filter(EXT_SVG, "SVG image")
    FILTER_PNG = qfile_filter(EXT_PNG, "PNG image")
    # Specific
    FILTER_CONSUMPTION = qfile_filter(EXT_CONSUMPTION, "Consumption History")
    FILTER_GPLINI = qfile_filter(EXT_INI, "GPL Pace Notes")
    FILTER_TPPN = qfile_filter(EXT_TPPN, "TinyPedal Pace Notes")
    FILTER_TPTN = qfile_filter(EXT_TPTN, "TinyPedal Track Notes")
    FILTER_TYRESTRATEGY = qfile_filter(EXT_TYRESTRATEGY, "TinyPedal Tyre Strategy")

    # Image file
    IMAGE_ICON = f"{PATH_IMAGE}icon{EXT_ICO}"
    IMAGE_TINYPEDAL = f"{PATH_IMAGE}icon{EXT_PNG}"
    IMAGE_COMPASS = f"{PATH_IMAGE}icon_compass{EXT_PNG}"
    IMAGE_INSTRUMENT = f"{PATH_IMAGE}icon_instrument{EXT_PNG}"
    IMAGE_STEERING_WHEEL = f"{PATH_IMAGE}icon_steering_wheel{EXT_PNG}"
    IMAGE_WEATHER = f"{PATH_IMAGE}icon_weather{EXT_PNG}"

    # Stats file
    STATS_DRIVER = f"driver{EXT_STATS}"

    # Log file
    LOG_APP = f"tinypedal{EXT_LOG}"
    LOG_PID = f"pid{EXT_LOG}"

    # Document file
    DOC_LICENSE = "LICENSE.txt"
    DOC_README = "README.md"
    DOC_THIRDPARTYNOTICES = f"{PATH_DOC}licenses/THIRDPARTYNOTICES.txt"
    DOC_CHANGELOG = f"{PATH_DOC}changelog.txt"
    DOC_USERGUIDE = f"{PATH_DOC}customization.md"
    DOC_CONTRIBUTORS = f"{PATH_DOC}contributors.md"
