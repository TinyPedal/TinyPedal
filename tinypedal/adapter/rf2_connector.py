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
rF2 API connector
"""

from __future__ import annotations

import ctypes
import logging
import threading
from time import monotonic, sleep
from typing import TYPE_CHECKING, Sequence

if __name__ == "__main__":  # local import check
    import sys
    sys.path.append(".")

if TYPE_CHECKING:  # for type checker only
    from pyRfactor2SharedMemory import rF2Type as rF2data
else:  # run time only
    from pyRfactor2SharedMemory import rF2data

from pyRfactor2SharedMemory.rF2MMap import (
    INVALID_INDEX,
    MAX_VEHICLES,
    MMapControl,
    rFactor2Constants,
)

logger = logging.getLogger(__name__)


def copy_struct(struct_data):
    """Allow to copy ctypes struct data with __slots__"""
    return type(struct_data).from_buffer_copy(
        ctypes.string_at(
            ctypes.byref(struct_data),
            ctypes.sizeof(struct_data),
        )
    )


def local_scoring_index(scor_veh: Sequence[rF2data.rF2VehicleScoring]) -> int:
    """Find local player scoring index

    Args:
        scor_veh: scoring mVehicles array.
    """
    for scor_idx, veh_info in enumerate(scor_veh):
        if veh_info.mIsPlayer:
            return scor_idx
    return INVALID_INDEX


class MMapDataSet:
    """Create mmap data set"""

    __slots__ = (
        "scor",
        "tele",
        "ext",
        "ffb",
    )

    def __init__(self) -> None:
        self.scor = MMapControl(rFactor2Constants.MM_SCORING_FILE_NAME, rF2data.rF2Scoring)
        self.tele = MMapControl(rFactor2Constants.MM_TELEMETRY_FILE_NAME, rF2data.rF2Telemetry)
        self.ext = MMapControl(rFactor2Constants.MM_EXTENDED_FILE_NAME, rF2data.rF2Extended)
        self.ffb = MMapControl(rFactor2Constants.MM_FORCE_FEEDBACK_FILE_NAME, rF2data.rF2ForceFeedback)

    def __del__(self):
        logger.info("sharedmemory: GC: MMapDataSet")

    def create_mmap(self, access_mode: int, rf2_pid: str) -> None:
        """Create mmap instance

        Args:
            access_mode: 0 = copy access, 1 = direct access.
            rf2_pid: rF2 Process ID for accessing server data.
        """
        self.scor.create(access_mode, rf2_pid)
        self.tele.create(access_mode, rf2_pid)
        self.ext.create(1, rf2_pid)
        self.ffb.create(1, rf2_pid)

    def close_mmap(self) -> None:
        """Close mmap instance"""
        self.scor.close()
        self.tele.close()
        self.ext.close()
        self.ffb.close()

    def update_mmap(self) -> None:
        """Update mmap data"""
        self.scor.update()
        self.tele.update()


class SyncData:
    """Synchronize data with player ID

    Attributes:
        dataset: mmap data set.
        paused: Data update state (boolean).
        override_player_index: Player index override state (boolean).
        player_scor_index: Local player scoring index.
        player_scor: Local player scoring data.
        player_tele: Local player telemetry data.
    """

    __slots__ = (
        "_updating",
        "_update_thread",
        "_event",
        "_tele_indexes",
        "paused",
        "override_player_index",
        "player_scor_index",
        "player_scor",
        "player_tele",
        "dataset",
    )

    def __init__(self) -> None:
        self._updating = False
        self._update_thread = None
        self._event = threading.Event()
        self._tele_indexes = {_index: _index for _index in range(128)}

        self.paused = False
        self.override_player_index = False
        self.player_scor_index = INVALID_INDEX
        self.player_scor = None
        self.player_tele = None
        self.dataset = MMapDataSet()

    def __del__(self):
        logger.info("sharedmemory: GC: SyncData")

    def __sync_player_data(self) -> bool:
        """Sync local player data

        Returns:
            False, if no valid player scoring index found.
            True, set player data.
        """
        if not self.override_player_index:
            # Update scoring index
            scor_idx = local_scoring_index(self.dataset.scor.data.mVehicles)
            if scor_idx == INVALID_INDEX:
                return False  # index not found, not synced
            self.player_scor_index = scor_idx
        # Set player data
        self.player_scor = self.dataset.scor.data.mVehicles[self.player_scor_index]
        self.player_tele = self.dataset.tele.data.mVehicles[self.sync_tele_index(self.player_scor_index)]
        return True  # found index, synced

    @staticmethod
    def __update_tele_indexes(tele_data: rF2data.rF2Telemetry, tele_indexes: dict) -> None:
        """Update telemetry player index dictionary for quick reference

        Telemetry index can be different from scoring index.
        Use mID matching to match telemetry index.

        Args:
            tele_data: Telemetry data.
            tele_indexes: Telemetry mID:index reference dictionary.
        """
        for tele_idx, veh_info in zip(range(tele_data.mNumVehicles), tele_data.mVehicles):
            tele_indexes[veh_info.mID] = tele_idx

    def sync_tele_index(self, scor_idx: int) -> int:
        """Sync telemetry index

        Use scoring index to find scoring mID,
        then match with telemetry mID in reference dictionary
        to find telemetry index.

        Args:
            scor_idx: Player scoring index.

        Returns:
            Player telemetry index.
        """
        return self._tele_indexes.get(
            self.dataset.scor.data.mVehicles[scor_idx].mID, INVALID_INDEX)

    def start(self, access_mode: int, rf2_pid: str) -> None:
        """Update & sync mmap data copy in separate thread

        Args:
            access_mode: 0 = copy access, 1 = direct access.
            rf2_pid: rF2 Process ID for accessing server data.
        """
        if self._updating:
            logger.warning("sharedmemory: UPDATING: already started")
        else:
            self._updating = True
            # Initialize mmap data
            self.dataset.create_mmap(access_mode, rf2_pid)
            self.__update_tele_indexes(self.dataset.tele.data, self._tele_indexes)
            if not self.__sync_player_data():
                self.player_scor = self.dataset.scor.data.mVehicles[INVALID_INDEX]
                self.player_tele = self.dataset.tele.data.mVehicles[INVALID_INDEX]
            # Setup updating thread
            self._event.clear()
            self._update_thread = threading.Thread(target=self.__update, daemon=True)
            self._update_thread.start()
            logger.info("sharedmemory: UPDATING: thread started")
            logger.info("sharedmemory: player index override: %s", self.override_player_index)
            logger.info("sharedmemory: server process ID: %s", rf2_pid if rf2_pid else "DISABLED")

    def stop(self) -> None:
        """Join and stop updating thread, close mmap"""
        if self._updating:
            self._event.set()
            self._updating = False
            self._update_thread.join()
            # Make final copy before close, otherwise mmap won't close if using direct access
            self.player_scor = copy_struct(self.player_scor)
            self.player_tele = copy_struct(self.player_tele)
            self.dataset.close_mmap()
        else:
            logger.warning("sharedmemory: UPDATING: already stopped")

    def __update(self) -> None:
        """Update synced player data"""
        self.paused = False  # make sure initial pause state is false
        _event_wait = self._event.wait
        freezed_version = 0  # store freezed update version number
        last_version_update = 0  # store last update version number
        last_update_time = 0.0
        data_freezed = True  # whether data is freezed
        reset_counter = 0
        update_delay = 0.5  # longer delay while inactive

        while not _event_wait(update_delay):
            self.dataset.update_mmap()
            self.__update_tele_indexes(self.dataset.tele.data, self._tele_indexes)
            # Update player data & index
            if not data_freezed:
                # Get player data
                data_synced = self.__sync_player_data()
                # Pause if local player index no longer exists, 5 tries
                if data_synced:
                    reset_counter = 0
                    self.paused = False
                elif reset_counter < 6:
                    reset_counter += 1
                    if reset_counter == 5:
                        self.player_scor_index = INVALID_INDEX
                        self.player_scor = self.dataset.scor.data.mVehicles[INVALID_INDEX]
                        self.player_tele = self.dataset.tele.data.mVehicles[INVALID_INDEX]
                        self.paused = True
                        logger.info("sharedmemory: UPDATING: player data paused")

            version_update = self.dataset.scor.data.mVersionUpdateEnd
            if last_version_update != version_update:
                last_version_update = version_update
                last_update_time = monotonic()

            if data_freezed:
                # Check while IN freeze state
                if freezed_version != last_version_update:
                    update_delay = 0.01
                    self.paused = data_freezed = False
                    logger.info(
                        "sharedmemory: UPDATING: resumed, data version %s",
                        last_version_update,
                    )
            # Check while NOT IN freeze state
            # Set freeze state if data stopped updating after 2s
            elif monotonic() - last_update_time > 2:
                update_delay = 0.5
                self.paused = data_freezed = True
                freezed_version = last_version_update
                logger.info(
                    "sharedmemory: UPDATING: paused, data version %s",
                    freezed_version,
                )

        logger.info("sharedmemory: UPDATING: thread stopped")


class RF2Info:
    """RF2 shared memory data output"""

    __slots__ = (
        "_sync",
        "_access_mode",
        "_rf2_pid",
        "_state_override",
        "_active_state",
        "_scor",
        "_tele",
        "_ext",
        "_ffb",
    )

    def __init__(self) -> None:
        self._sync = SyncData()
        self._access_mode = 0
        self._rf2_pid = ""
        self._state_override = False
        self._active_state = False
        # Assign mmap instance
        self._scor = self._sync.dataset.scor
        self._tele = self._sync.dataset.tele
        self._ext = self._sync.dataset.ext
        self._ffb = self._sync.dataset.ffb

    def __del__(self):
        logger.info("sharedmemory: GC: RF2Info")

    def start(self) -> None:
        """Start data updating thread"""
        self._sync.start(self._access_mode, self._rf2_pid)

    def stop(self) -> None:
        """Stop data updating thread"""
        self._sync.stop()

    def setPID(self, pid: str = "") -> None:
        """Set rF2 process ID for connecting to server data"""
        self._rf2_pid = str(pid)

    def setMode(self, mode: int = 0) -> None:
        """Set rF2 mmap access mode

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
        self._sync.player_scor_index = min(max(index, INVALID_INDEX), MAX_VEHICLES - 1)

    @property
    def rf2ScorInfo(self) -> rF2data.rF2ScoringInfo:
        """rF2 scoring info data"""
        return self._scor.data.mScoringInfo

    def rf2ScorVeh(self, index: int | None = None) -> rF2data.rF2VehicleScoring:
        """rF2 scoring vehicle data

        Specify index for specific player.

        Args:
            index: None for local player.
        """
        if index is None:
            return self._sync.player_scor
        return self._scor.data.mVehicles[index]

    def rf2TeleVeh(self, index: int | None = None) -> rF2data.rF2VehicleTelemetry:
        """rF2 telemetry vehicle data

        Specify index for specific player.

        Args:
            index: None for local player.
        """
        if index is None:
            return self._sync.player_tele
        return self._tele.data.mVehicles[self._sync.sync_tele_index(index)]

    @property
    def rf2Ext(self) -> rF2data.rF2Extended:
        """rF2 extended data"""
        return self._ext.data

    @property
    def rf2Ffb(self) -> rF2data.rF2ForceFeedback:
        """rF2 force feedback data"""
        return self._ffb.data

    @property
    def playerIndex(self) -> int:
        """rF2 local player's scoring index"""
        return self._sync.player_scor_index

    def isPlayer(self, index: int) -> bool:
        """Check whether index is player"""
        if self._sync.override_player_index:
            return self._sync.player_scor_index == index
        return self._scor.data.mVehicles[index].mIsPlayer

    @property
    def isPaused(self) -> bool:
        """Check whether data stopped updating"""
        return self._sync.paused or self._sync.player_scor_index < 0

    @property
    def isActive(self) -> bool:
        """Check whether in active (driving or overriding) state"""
        if self._state_override:
            return self._active_state
        return not self._sync.paused and self._sync.player_scor_index >= 0 and (
            self.rf2ScorInfo.mInRealtime
            or self.rf2TeleVeh().mIgnitionStarter > 0
        )

    @property
    def identifier(self) -> str:
        """Identify sim name"""
        name = self.rf2ScorInfo.mPlrFileName
        if b"Settings" in name:
            return "LMU"
        if name:
            return "RF2"
        return ""


def test_api():
    """API test run"""
    # Add logger
    test_handler = logging.StreamHandler()
    logger.setLevel(logging.INFO)
    logger.addHandler(test_handler)

    # Test run
    SEPARATOR = "=" * 50
    print("Test API - Start")
    info = RF2Info()
    info.setMode(1)  # set direct access
    info.setPID("")
    info.setPlayerOverride(True)  # enable player override
    info.setPlayerIndex(0)  # set player index to 0
    info.start()
    sleep(0.2)

    print(SEPARATOR)
    print("Test API - Restart")
    info.stop()
    info.setMode()  # set copy access
    info.setPlayerOverride()  # disable player override
    info.start()

    print(SEPARATOR)
    print("Test API - Read")
    version = info.rf2Ext.mVersion.decode()
    driver = info.rf2ScorVeh(0).mDriverName.decode(encoding="iso-8859-1")
    track = info.rf2ScorInfo.mTrackName.decode(encoding="iso-8859-1")
    print(f"plugin version: {version if version else 'not running'}")
    print(f"driver name   : {driver if version else 'not running'}")
    print(f"track name    : {track if version else 'not running'}")

    print(SEPARATOR)
    print("Test API - Close")
    info.stop()


if __name__ == "__main__":
    test_api()
