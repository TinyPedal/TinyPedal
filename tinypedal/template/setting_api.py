#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Default API setting template
"""

API_DEFAULT = {
    "api_lmu": {
        "access_mode": 0,
        "enable_active_state_override": False,
        "active_state": True,
        "enable_player_index_override": False,
        "player_index": -1,
        "character_encoding": "UTF-8",
        "enable_restapi_access": True,
        "restapi_update_interval": 200,
        "url_host": "localhost",
        "url_port": 6397,
        "connection_timeout": 1,
        "connection_retry": 3,
        "connection_retry_delay": 1,
        "enable_energy_remaining": True,
        "enable_garage_setup_info": True,
        "enable_session_info": True,
        "enable_vehicle_info": True,
        "enable_weather_info": True,
    },
    "api_rf2": {
        "access_mode": 0,
        "process_id": "",
        "enable_active_state_override": False,
        "active_state": True,
        "enable_player_index_override": False,
        "player_index": -1,
        "character_encoding": "UTF-8",
        "enable_restapi_access": True,
        "restapi_update_interval": 200,
        "url_host": "localhost",
        "url_port": 5397,
        "connection_timeout": 1,
        "connection_retry": 3,
        "connection_retry_delay": 1,
        "enable_garage_setup_info": True,
        "enable_session_info": True,
        "enable_weather_info": True,
    },
}
