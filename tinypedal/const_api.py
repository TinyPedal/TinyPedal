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
API constants
"""

from types import MappingProxyType

from .const_app import PLATFORM

API_LMU_NAME = "Le Mans Ultimate"
API_LMU_ALIAS = "LMU"
API_LMU_CONFIG = "api_lmu"

API_LMULEGACY_NAME = "Le Mans Ultimate (legacy)"
API_LMULEGACY_ALIAS = "LMU*"
API_LMULEGACY_CONFIG = "api_lmu"

API_RF2_NAME = "rFactor 2"
API_RF2_ALIAS = "RF2"
API_RF2_CONFIG = "api_rf2"

# DEFAULT API
if PLATFORM == "Windows":
    API_DEFAULT_NAME = API_LMU_NAME
else:
    API_DEFAULT_NAME = API_LMULEGACY_NAME

# Reference
API_MAP_ALIAS = MappingProxyType({
    API_LMU_NAME: API_LMU_ALIAS,
    API_LMULEGACY_NAME: API_LMULEGACY_ALIAS,
    API_RF2_NAME: API_RF2_ALIAS,
})
API_MAP_CONFIG = MappingProxyType({
    API_LMU_NAME: API_LMU_CONFIG,
    API_LMULEGACY_NAME: API_LMULEGACY_CONFIG,
    API_RF2_NAME: API_RF2_CONFIG,
})
