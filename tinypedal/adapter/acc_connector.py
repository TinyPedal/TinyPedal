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
ACC API connector
"""

from ..constant import API
from ..validator import bytes_decoder
from . import acc_reader, acc_sharedmemory, acc_udpapi
from ._connector import APIDataReader, Connector


class SimACC(Connector):
    """Assetto Corsa Competizione - ACC Native Sharedmemory API"""

    NAME = API.NAME_ACC
    LEGACY = False
    __slots__ = (
        # Primary API
        "_shmmapi",
        # Secondary API
        "_udpapi",
    )

    def __init__(self):
        self._shmmapi = acc_sharedmemory.ACCInfo()
        self._udpapi = acc_udpapi.UDPAPIConnector()

    def start(self):
        self._shmmapi.start()  # 1 load first
        self._udpapi.start()  # 2

    def stop(self):
        self._udpapi.stop()  # 1 unload first
        self._shmmapi.stop()  # 2

    def reader(self) -> APIDataReader:
        shmm = self._shmmapi
        udp = self._udpapi.output
        return APIDataReader(
            acc_reader.State(shmm, udp),
            acc_reader.Brake(shmm, udp),
            acc_reader.ElectricMotor(shmm, udp),
            acc_reader.Engine(shmm, udp),
            acc_reader.Inputs(shmm, udp),
            acc_reader.Lap(shmm, udp),
            acc_reader.Session(shmm, udp),
            acc_reader.Switch(shmm, udp),
            acc_reader.Timing(shmm, udp),
            acc_reader.Tyre(shmm, udp),
            acc_reader.Vehicle(shmm, udp),
            acc_reader.Wheel(shmm, udp),
        )

    def setup(self, config: dict):
        self._shmmapi.setMode(config["access_mode"])
        self._shmmapi.setStateOverride(config["enable_active_state_override"])
        self._shmmapi.setActiveState(config["active_state"])
        self._shmmapi.setPlayerOverride(config["enable_player_index_override"])
        self._shmmapi.setPlayerIndex(config["player_index"])
        self._udpapi.setConnection(config.copy())
        acc_reader.tostr = bytes_decoder(config["character_encoding"])
