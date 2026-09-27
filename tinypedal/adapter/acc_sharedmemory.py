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
ACC sharedmemory API connector
"""

from __future__ import annotations

import ctypes
import logging
import threading
from time import monotonic
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:  # for type checker only
    from thirdparty.pyACCSharedMemory import acc_data, acc_enum, acc_udp
    from thirdparty.pyACCSharedMemory.acc_data import ACCConstants
    from thirdparty.pyACCSharedMemory.acc_mmap import MMapControl
else:  # run time only
    from pyACCSharedMemory import acc_data, acc_enum, acc_udp
    from pyACCSharedMemory.acc_data import ACCConstants
    from pyACCSharedMemory.acc_mmap import MMapControl

from ..process.timing import LastSectorTime, TimeScale, ValidLapStatus
from ..process.vehicle import LastImpact, VehicleOrientation, VehicleSpeed

logger = logging.getLogger(__name__)

# Constant & Enum
INVALID_INDEX = ACCConstants.INVALID_CAR_INDEX


def copy_struct(struct_data):
    """Allow to copy ctypes struct data with __slots__"""
    return type(struct_data).from_buffer_copy(
        ctypes.string_at(
            ctypes.byref(struct_data),
            ctypes.sizeof(struct_data),
        )
    )


def local_player_index_by_id(player_car_id: int, car_id_list: Sequence[int]) -> int:
    """Find local player index by car id"""
    for index, car_id in enumerate(car_id_list):
        if car_id == player_car_id:
            if INVALID_INDEX <= index:
                return index
            break
    return INVALID_INDEX


class MMapDataSet:
    """Create mmap data set"""

    __slots__ = (
        "phys",
        "ghfx",
        "stat",
    )

    def __init__(self) -> None:
        self.phys = MMapControl(ACCConstants.MM_PHYSICS_FILE_NAME, acc_data.ACCPhysics)
        self.ghfx = MMapControl(ACCConstants.MM_GRAPHICS_FILE_NAME, acc_data.ACCGraphics)
        self.stat = MMapControl(ACCConstants.MM_STATIC_FILE_NAME, acc_data.ACCStatic)

    def __del__(self):
        logger.info("sharedmemory: GC: MMapDataSet")

    def create_mmap(self, access_mode: int) -> None:
        """Create mmap instance

        Args:
            access_mode: 0 = copy access, 1 = direct access.
        """
        self.phys.create(access_mode)
        self.ghfx.create(access_mode)
        self.stat.create(1)

    def close_mmap(self) -> None:
        """Close mmap instance"""
        self.phys.close()
        self.ghfx.close()
        self.stat.close()

    def update_mmap(self) -> None:
        """Update mmap data"""
        self.phys.update()
        self.ghfx.update()


class SyncData:
    """Synchronize data with player ID

    Attributes:
        dataset: mmap data set.
        paused: Is API data paused.
        synced: Is player data synced.
        resets: Number of player vehicle resets.
        override_player_index: is player index overidden.
        player_car_index: Local player car index.
    """

    __slots__ = (
        "_updating",
        "_update_thread",
        "_event",
        "paused",
        "synced",
        "resets",
        "override_player_index",
        "player_car_id",
        "player_car_index",
        "dataset",
        "player_phys",
        "player_ghfx",
        "player_stat",
        "elapsed_time",
    )

    def __init__(self) -> None:
        self._updating = False
        self._update_thread = None
        self._event = threading.Event()

        self.paused = False
        self.synced = False
        self.resets = 0
        self.override_player_index = False
        self.player_car_id = INVALID_INDEX
        self.player_car_index = INVALID_INDEX
        self.dataset = MMapDataSet()
        self.player_phys = None
        self.player_ghfx = None
        self.player_stat = None
        self.elapsed_time = 0.0

    def __del__(self):
        logger.info("sharedmemory: GC: SyncData")

    def start(self, access_mode: int) -> None:
        """Update & sync mmap data copy in separate thread

        Args:
            access_mode: 0 = copy access, 1 = direct access.
        """
        if self._updating:
            logger.warning("sharedmemory: UPDATING: already started")
        else:
            self._updating = True
            # Initialize mmap data
            self.dataset.create_mmap(access_mode)
            self.player_phys = self.dataset.phys.data
            self.player_ghfx = self.dataset.ghfx.data
            self.player_stat = self.dataset.stat.data
            # Setup updating thread
            self._event.clear()
            self._update_thread = threading.Thread(target=self.__update, daemon=True)
            self._update_thread.start()
            logger.info("sharedmemory: UPDATING: thread started")
            logger.info("sharedmemory: player index override: %s", self.override_player_index)

    def stop(self) -> None:
        """Join and stop updating thread, close mmap"""
        if self._updating:
            self._event.set()
            self._updating = False
            self._update_thread.join()
            # Make final copy before close, otherwise mmap won't close if using direct access
            self.player_phys = copy_struct(self.player_phys)
            self.player_ghfx = copy_struct(self.player_ghfx)
            self.player_stat = copy_struct(self.player_stat)
            self.dataset.close_mmap()
        else:
            logger.warning("sharedmemory: UPDATING: already stopped")

    def __update(self) -> None:
        """Update synced player data"""
        self.paused = True
        self.synced = False
        self.resets = 0

        _event_wait = self._event.wait
        freezed_timestamp = 0  # store freezed timestamp
        last_session_timestamp = 0  # store last timestamp
        last_update_time = 0.0
        data_freezed = True  # whether data is freezed

        last_stint_distance = 0.0
        last_car_id = INVALID_INDEX
        reset_counter = 0
        update_delay = 0.5  # longer delay while inactive

        self.elapsed_time = 0.0
        session_timestamp = 0.0
        last_mono_time = 0.0

        while not _event_wait(update_delay):
            self.dataset.update_mmap()
            session_timestamp = self.player_ghfx.packetId

            # Update player data & index
            if not data_freezed:
                # Get player index
                if self.override_player_index:
                    player_car_id = self.player_car_id
                else:
                    player_car_id = self.player_ghfx.playerCarID
                self.player_car_index = local_player_index_by_id(
                    player_car_id, self.player_ghfx.carIDs
                )
                data_synced = self.player_car_index != INVALID_INDEX
                # Pause if local player index no longer exists, 5 tries
                if data_synced:
                    reset_counter = 0
                    self.synced = True
                elif reset_counter < 6:
                    reset_counter += 1
                    if reset_counter == 5:
                        self.player_car_index = INVALID_INDEX
                        self.synced = False
                        logger.info("sharedmemory: UPDATING: player data paused")

            if last_session_timestamp != session_timestamp:
                # Calculate delta & elapsed time
                mono_time = monotonic()
                self.elapsed_time += min(mono_time - last_mono_time, 0.1)
                last_mono_time = mono_time

                # Check resets
                stint_distance = self.player_ghfx.distanceTraveled
                car_id = self.player_ghfx.playerCarID
                if (
                    last_session_timestamp > session_timestamp  # session changed
                    or last_stint_distance > stint_distance  # returned to garage
                    or last_car_id != car_id  # changed car id
                ):
                    self.elapsed_time = 0.0
                    self.resets += 1

                last_update_time = monotonic()
                last_session_timestamp = session_timestamp
                last_stint_distance = stint_distance
                last_car_id = car_id

            if data_freezed:
                # Check while IN freeze state
                if freezed_timestamp != last_session_timestamp:
                    update_delay = 0.01
                    self.paused = data_freezed = False
                    logger.info(
                        "sharedmemory: UPDATING: resumed, data timestamp %s",
                        last_session_timestamp,
                    )
            # Check while NOT IN freeze state
            # Set freeze state if data stopped updating after 2s
            elif monotonic() - last_update_time > 2:
                update_delay = 0.5
                self.paused = data_freezed = True
                self.synced = False
                freezed_timestamp = last_session_timestamp
                logger.info(
                    "sharedmemory: UPDATING: paused, data timestamp %s",
                    freezed_timestamp,
                )

        logger.info("sharedmemory: UPDATING: thread stopped")


class ACCInfo:
    """ACC shared memory data output"""

    __slots__ = (
        "_sync",
        "_access_mode",
        "_state_override",
        "_active_state",
        "_last_impact",
        "_last_sector_time",
        "_time_scale",
        "_valid_lap_status",
        "_vehicle_yaw",
        "_vehicle_speed",
    )

    def __init__(self) -> None:
        self._sync = SyncData()
        self._access_mode = 0
        self._state_override = False
        self._active_state = False
        self._last_impact = LastImpact()
        self._last_sector_time = LastSectorTime()
        self._time_scale = TimeScale()
        self._valid_lap_status = ValidLapStatus()
        self._vehicle_yaw = tuple(VehicleOrientation() for _ in range(ACCConstants.MAX_MAPPED_VEHICLES))
        self._vehicle_speed = tuple(VehicleSpeed() for _ in range(ACCConstants.MAX_MAPPED_VEHICLES))

    def __del__(self):
        logger.info("sharedmemory: GC: ACCInfo")

    def start(self) -> None:
        """Start data updating thread"""
        self._sync.start(self._access_mode)

    def stop(self) -> None:
        """Stop data updating thread"""
        self._sync.stop()

    def setMode(self, mode: int = 0) -> None:
        """Set mmap access mode

        Args:
            mode: 0 = copy access, 1 = direct access
        """
        self._access_mode = mode

    def setStateOverride(self, state: bool = False) -> None:
        """Enable state override"""
        self._state_override = state

    def setActiveState(self, state: bool = False) -> None:
        """Set state override"""
        self._active_state = state

    def setPlayerOverride(self, state: bool = False) -> None:
        """Enable player index override state"""
        self._sync.override_player_index = state

    def setPlayerIndex(self, index: int = INVALID_INDEX) -> None:
        """Manual override player index"""
        self._sync.player_car_id = max(index, INVALID_INDEX)

    def accVehicleYaw(self, index: int | None = None) -> float:
        """ACC vehicle yaw"""
        if index is None:
            index = self._sync.player_car_index
        pos = self._sync.player_ghfx.carCoordinates[index]
        return self._vehicle_yaw[index].update(pos.x, pos.z)

    def accVehicleSpeed(self, index: int | None = None) -> float:
        """ACC vehicle speed"""
        if index is None:
            index = self._sync.player_car_index
        pos = self._sync.player_ghfx.carCoordinates[index]
        return self._vehicle_speed[index].update(self._sync.elapsed_time, pos.x, pos.z)

    @property
    def accTimeScale(self) -> TimeScale:
        """ACC time scale"""
        data = self._sync.player_ghfx
        return self._time_scale.update(self._sync.elapsed_time, data.timeOfDay)

    @property
    def accLastSectorTime(self) -> LastSectorTime:
        """ACC last sector time"""
        data = self._sync.player_ghfx
        return self._last_sector_time.update(
            data.currentSectorIndex,
            data.lastSectorTime * 0.001,
            data.iLastTime * 0.001,
            data.isValidLap,
        )

    @property
    def accValidLap(self) -> ValidLapStatus:
        """ACC valid lap status"""
        data = self._sync.player_ghfx
        return self._valid_lap_status.update(data.iCurrentTime, data.isValidLap, self._sync.resets)

    @property
    def accLastImpact(self) -> LastImpact:
        """ACC last impact data"""
        return self._last_impact.update(self._sync.elapsed_time, *self._sync.player_phys.carDamage)

    @property
    def accPhysicsInfo(self) -> acc_data.ACCPhysics:
        """ACC physics info data"""
        return self._sync.player_phys

    @property
    def accGraphicsInfo(self) -> acc_data.ACCGraphics:
        """ACC graphics info data"""
        return self._sync.player_ghfx

    @property
    def accStaticInfo(self) -> acc_data.ACCStatic:
        """ACC static info data"""
        return self._sync.player_stat

    @property
    def playerIndex(self) -> int:
        """Local player's car index"""
        return self._sync.player_car_index

    @property
    def isPaused(self) -> bool:
        """Check whether data stopped updating"""
        return self._sync.paused

    @property
    def isActive(self) -> bool:
        """Check whether in active (driving or overriding) state"""
        if self._state_override:
            return self._active_state
        if self._sync.override_player_index:  # spectate only
            return self.accVehicleSpeed() > 0
        return (
            self._sync.synced
            and self._sync.player_car_index >= 0
            and self._sync.player_phys.currentMaxRPM > 0
        )

    @property
    def vehicleResets(self) -> int:
        """Number of player vehicle resets"""
        return self._sync.resets

    @property
    def elapsed(self) -> float:
        """Number of player vehicle resets"""
        return self._sync.elapsed_time
