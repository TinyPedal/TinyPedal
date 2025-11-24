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
Module info
"""

from __future__ import annotations

from array import array
from collections import deque
from typing import Mapping, NamedTuple

from .const_common import (
    DELTA_DEFAULT,
    EMPTY_DICT,
    MAX_METERS,
    MAX_SECONDS,
    MAX_VEHICLES,
    REL_TIME_DEFAULT,
    WHEELS_ZERO,
)


class ConsumptionDataSet(NamedTuple):
    """Consumption history data set"""

    lapNumber: int = 0
    isValidLap: int = 0
    lapTimeLast: float = 0.0
    lastLapUsedFuel: float = 0.0
    lastLapUsedEnergy: float = 0.0
    batteryDrainLast: float = 0.0
    batteryRegenLast: float = 0.0
    tyreAvgWearLast: float = 0.0
    capacityFuel: float = 0.0


class DeltaLapTime(array):
    """Delta lap time history data"""

    __slots__ = ()

    def update(self, lap_start: float, lap_elapsed: float, laptime_last: float):
        """Update delta lap time history"""
        # Check 2 sec after start new lap (for validating last lap time)
        # Store lap start time in index 5
        if self[5] != lap_start and lap_elapsed - lap_start > 2:
            if self[5] < lap_start:
                self[0], self[1], self[2], self[3] = self[1], self[2], self[3], self[4]
                if laptime_last > 0:  # valid last lap time
                    self[4] = laptime_last
                else:
                    self[4] = 0.0
            else:  # reset all laptime
                self[0] = self[1] = self[2] = self[3] = self[4] = 0.0
            self[5] = lap_start

    def delta(self, target: DeltaLapTime, max_output: int):
        """Generate delta from target player's lap time data set"""
        for index in range(5 - max_output, 5):  # max 5 records
            if target[index] > 0 < self[index]:  # check invalid lap time
                yield target[index] - self[index]
            else:
                yield MAX_SECONDS


class VehiclePitTimer:
    """Vehicle pit timer"""

    __slots__ = (
        "elapsed",
        "stopped",
        "pitting",
        "lap_stopped",
        "_slot_id",
        "_pitin_time",
        "_pitstop_time",
        "_last_state",
        "_last_pit_lap",
    )

    def __init__(self):
        self.elapsed: float = 0.0
        self.stopped: float = 0.0
        self.pitting: bool = False
        self.lap_stopped: int = 0
        self._slot_id: int = -1
        self._pitin_time: float = 0.0
        self._pitstop_time: float = 0.0
        self._last_state: int = 0
        self._last_pit_lap: int = 99999

    def update(self, slot_id: int, in_pit: int, elapsed_time: float, laps_done: int, speed: float):
        """Calculate pit time

        Pit state: 0 = not in pit, 1 = in pit, 2 = in garage.
        """
        # Reset if slot (vehicle) id changed
        if self._slot_id != slot_id:
            self._slot_id = slot_id
            self.elapsed = 0.0
            self.stopped = 0.0
            self.pitting = False
            self._pitin_time = elapsed_time
            self._pitstop_time = elapsed_time
            self._last_state = 0
            self._last_pit_lap = laps_done
        # Reset if session changed
        if self._last_pit_lap > laps_done:
            self._last_pit_lap = laps_done
        # Pit status check
        if self._last_state != in_pit:
            self._last_state = in_pit
            self._pitin_time = elapsed_time
            self._pitstop_time = elapsed_time
            if in_pit:  # reset after enter pit
                self.elapsed = 0.0
                self.stopped = 0.0
        if in_pit:
            # Ignore pit timer in garage
            if in_pit == 2:
                self.elapsed = 0.0
                self.stopped = 0.0
                self._last_pit_lap = laps_done
            # Calculating time while in pit
            else:
                # Total elapsed time in pit
                self.elapsed += elapsed_time - self._pitin_time
                # Total stopped time in pit
                if speed < 0.1:
                    self.stopped += elapsed_time - self._pitstop_time
            # Reset delta
            self._pitin_time = elapsed_time
            self._pitstop_time = elapsed_time
            # Save last in pit lap number
            # Pit state can desync, wait minimum 2 seconds before update
            if self.elapsed > 2 and self.stopped > 1:  # stop for more than 1 seconds
                self._last_pit_lap = laps_done
        # Check whether is pitting lap
        self.pitting = (in_pit > 0 or laps_done == self._last_pit_lap)
        self.lap_stopped = self._last_pit_lap


class VehicleDataSet:
    """Vehicle data set"""

    __slots__ = (
        "isPlayer",
        "positionOverall",
        "positionInClass",
        "qualifyOverall",
        "qualifyInClass",
        "driverName",
        "vehicleName",
        "vehicleClass",
        "classBestLapTime",
        "bestLapTime",
        "lastLapTime",
        "currentLapProgress",
        "totalLapProgress",
        "gapBehindNext",
        "gapBehindNextInClass",
        "gapBehindLeader",
        "gapBehindLeaderInClass",
        "isLapped",
        "isYellow",
        "inPit",
        "isClassFastestLastLap",
        "numPitStops",
        "pitRequested",
        "tireCompoundFront",
        "tireCompoundRear",
        "relativeOrientationRadians",
        "relativeStraightDistance",
        "worldPositionX",
        "worldPositionY",
        "relativeRotatedPositionX",
        "relativeRotatedPositionY",
        "vehicleIntegrity",
        "energyRemaining",
        "estimatedStintLaps",
        "currentStintLaps",
        "pitTimer",
        "lapTimeHistory",
    )

    def __init__(self):
        self.isPlayer: bool = False
        self.positionOverall: int = 0
        self.positionInClass: int = 0
        self.qualifyOverall: int = 0
        self.qualifyInClass: int = 0
        self.driverName: str = ""
        self.vehicleName: str = ""
        self.vehicleClass: str = ""
        self.classBestLapTime: float = MAX_SECONDS
        self.bestLapTime: float = MAX_SECONDS
        self.lastLapTime: float = MAX_SECONDS
        self.currentLapProgress: float = 0.0
        self.totalLapProgress: float = 0.0
        self.gapBehindNext: float = 0.0
        self.gapBehindNextInClass: float = 0.0
        self.gapBehindLeader: float = 0.0
        self.gapBehindLeaderInClass: float = 0.0
        self.isLapped: float = 0.0
        self.isYellow: bool = False
        self.inPit: int = 0
        self.isClassFastestLastLap: bool = False
        self.numPitStops: int = 0
        self.pitRequested: bool = False
        self.tireCompoundFront: str = ""
        self.tireCompoundRear: str = ""
        self.relativeOrientationRadians: float = 0.0
        self.relativeStraightDistance: float = 0.0
        self.worldPositionX: float = 0.0
        self.worldPositionY: float = 0.0
        self.relativeRotatedPositionX: float = 0.0
        self.relativeRotatedPositionY: float = 0.0
        self.vehicleIntegrity: float = 0.0
        self.energyRemaining: float = 0.0
        self.estimatedStintLaps: float = 0.0
        self.currentStintLaps: int = 0
        self.pitTimer: VehiclePitTimer = VehiclePitTimer()
        self.lapTimeHistory: DeltaLapTime = DeltaLapTime("d", [0.0] * 6)


class DeltaInfo:
    """Delta module output data"""

    __slots__ = (
        "deltaBestData",
        "deltaBest",
        "deltaLast",
        "deltaSession",
        "deltaStint",
        "isValidLap",
        "lapTimeCurrent",
        "lapTimeLast",
        "lapTimeBest",
        "lapTimeEstimated",
        "lapTimeSession",
        "lapTimeStint",
        "lapTimePace",
        "lapDistance",
    )

    def __init__(self):
        self.deltaBestData: tuple = DELTA_DEFAULT
        self.deltaBest: float = 0.0
        self.deltaLast: float = 0.0
        self.deltaSession: float = 0.0
        self.deltaStint: float = 0.0
        self.isValidLap: bool = False
        self.lapTimeCurrent: float = 0.0
        self.lapTimeLast: float = 0.0
        self.lapTimeBest: float = 0.0
        self.lapTimeEstimated: float = 0.0
        self.lapTimeSession: float = 0.0
        self.lapTimeStint: float = 0.0
        self.lapTimePace: float = 0.0
        self.lapDistance: float = 0.0


class ForceInfo:
    """Force module output data"""

    __slots__ = (
        "lgtGForceRaw",
        "latGForceRaw",
        "maxAvgLatGForce",
        "maxLgtGForce",
        "maxLatGForce",
        "downForceFront",
        "downForceRear",
        "downForceRatio",
        "brakingRate",
        "transientMaxBrakingRate",
        "maxBrakingRate",
        "deltaBrakingRate",
    )

    def __init__(self):
        self.lgtGForceRaw: float = 0.0
        self.latGForceRaw: float = 0.0
        self.maxAvgLatGForce: float = 0.0
        self.maxLgtGForce: float = 0.0
        self.maxLatGForce: float = 0.0
        self.downForceFront: float = 0.0
        self.downForceRear: float = 0.0
        self.downForceRatio: float = 0.0
        self.brakingRate: float = 0.0
        self.transientMaxBrakingRate: float = 0.0
        self.maxBrakingRate: float = 0.0
        self.deltaBrakingRate: float = 0.0


class FuelInfo:
    """Fuel module output data"""

    __slots__ = (
        "capacity",
        "amountStart",
        "amountCurrent",
        "amountUsedCurrent",
        "amountEndStint",
        "neededRelative",
        "neededAbsolute",
        "lastLapConsumption",
        "estimatedConsumption",
        "estimatedValidConsumption",
        "estimatedLaps",
        "estimatedMinutes",
        "estimatedNumPitStopsEnd",
        "estimatedNumPitStopsEarly",
        "deltaConsumption",
        "oneLessPitConsumption",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset"""
        self.capacity: float = 0.0
        self.amountStart: float = 0.0
        self.amountCurrent: float = 0.0
        self.amountUsedCurrent: float = 0.0
        self.amountEndStint: float = 0.0
        self.neededRelative: float = 0.0
        self.neededAbsolute: float = 0.0
        self.lastLapConsumption: float = 0.0
        self.estimatedConsumption: float = 0.0
        self.estimatedValidConsumption: float = 0.0
        self.estimatedLaps: float = 0.0
        self.estimatedMinutes: float = 0.0
        self.estimatedNumPitStopsEnd: float = 0.0
        self.estimatedNumPitStopsEarly: float = 0.0
        self.deltaConsumption: float = 0.0
        self.oneLessPitConsumption: float = 0.0


class HistoryInfo:
    """History output data"""

    __slots__ = (
        "consumptionDataName",
        "consumptionDataVersion",
        "consumptionDataSet",
    )

    def __init__(self):
        self.consumptionDataName: str = ""
        self.consumptionDataVersion: int = 0
        self.consumptionDataSet: deque[ConsumptionDataSet] = deque([ConsumptionDataSet()], 100)

    def reset_consumption(self):
        """Reset consumption data"""
        self.consumptionDataName = ""
        self.consumptionDataVersion = 0
        self.consumptionDataSet.clear()
        self.consumptionDataSet.appendleft(ConsumptionDataSet())


class HybridInfo:
    """Hybrid module output data"""

    __slots__ = (
        "batteryCharge",
        "batteryDrain",
        "batteryRegen",
        "batteryDrainLast",
        "batteryRegenLast",
        "batteryNetChange",
        "motorActiveTimer",
        "motorInactiveTimer",
        "motorState",
        "fuelEnergyRatio",
        "fuelEnergyBias",
    )

    def __init__(self):
        self.batteryCharge: float = 0.0
        self.batteryDrain: float = 0.0
        self.batteryRegen: float = 0.0
        self.batteryDrainLast: float = 0.0
        self.batteryRegenLast: float = 0.0
        self.batteryNetChange: float = 0.0
        self.motorActiveTimer: float = 0.0
        self.motorInactiveTimer: float = 0.0
        self.motorState: int = 0
        self.fuelEnergyRatio: float = 0.0
        self.fuelEnergyBias: float = 0.0


class MappingInfo:
    """Mapping module output data"""

    __slots__ = (
        "coordinates",
        "elevations",
        "sectors",
        "lastModified",
        "pitEntryPosition",
        "pitExitPosition",
        "pitLaneLength",
        "pitSpeedLimit",
        "pitPassTime",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset"""
        self.coordinates: tuple[tuple[float, float], ...] | None = None
        self.elevations: tuple[tuple[float, float], ...] | None = None
        self.sectors: tuple[int, int] | None = None
        self.lastModified: float = 0.0
        self.pitEntryPosition: float = 0.0
        self.pitExitPosition: float = 0.0
        self.pitLaneLength: float = 0.0
        self.pitSpeedLimit: float = 0.0
        self.pitPassTime: float = 0.0


class NotesInfo:
    """Notes module output data"""

    __slots__ = (
        "currentIndex",
        "currentNote",
        "nextIndex",
        "nextNote",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset"""
        self.currentIndex: int = 0
        self.currentNote: Mapping[str, float | str] = EMPTY_DICT
        self.nextIndex: int = 0
        self.nextNote: Mapping[str, float | str] = EMPTY_DICT


class RelativeInfo:
    """Relative module output data"""

    __slots__ = (
        "relative",
        "standings",
        "classes",
        "drawOrder",
    )

    def __init__(self):
        self.relative: list[list] = [REL_TIME_DEFAULT]
        self.standings: list[int] = [-1]
        self.classes: list[list] = [[0, 1, "", 0.0, -1, -1, -1, False]]
        self.drawOrder: list = [0]


class SectorsInfo:
    """Sectors module output data"""

    __slots__ = (
        "noDeltaSector",
        "sectorIndex",
        "sectorPrev",
        "sectorBestTB",
        "sectorBestPB",
        "deltaSectorBestPB",
        "deltaSectorBestTB",
    )

    def __init__(self):
        self.noDeltaSector: bool = True
        self.sectorIndex: int = -1
        self.sectorPrev: list[float] = [MAX_SECONDS] * 3
        self.sectorBestTB: list[float] = [MAX_SECONDS] * 3
        self.sectorBestPB: list[float] = [MAX_SECONDS] * 3
        self.deltaSectorBestPB: list[float] = [MAX_SECONDS] * 3
        self.deltaSectorBestTB: list[float] = [MAX_SECONDS] * 3


class StatsInfo:
    """Stats module output data"""

    __slots__ = (
        "metersDriven",
    )

    def __init__(self):
        self.metersDriven: float = 0.0


class VehiclesInfo:
    """Vehicles module output data"""

    __slots__ = (
        "totalVehicles",
        "leaderIndex",
        "playerIndex",
        "dataSet",
        "dataSetVersion",
        "nearestLine",
        "nearestTraffic",
        "nearestYellowAhead",
        "nearestYellowBehind",
        "leaderBestLapTime",
    )

    def __init__(self):
        self.totalVehicles: int = 0
        self.leaderIndex: int = 0
        self.playerIndex: int = -1
        self.dataSet: tuple[VehicleDataSet, ...] = tuple(
            VehicleDataSet() for _ in range(MAX_VEHICLES)
        )
        self.dataSetVersion: int = -1
        self.nearestLine: float = MAX_METERS
        self.nearestTraffic: float = MAX_SECONDS
        self.nearestYellowAhead: float = MAX_METERS
        self.nearestYellowBehind: float = -MAX_METERS
        self.leaderBestLapTime: float = MAX_SECONDS


class WheelsInfo:
    """Wheels module output data"""

    __slots__ = (
        "lockingPercentFront",
        "lockingPercentRear",
        "corneringRadius",
        "slipRatio",
        "currentTreadDepth",
        "lastLapTreadWear",
        "estimatedTreadWear",
        "estimatedValidTreadWear",
        "maxBrakeThickness",
        "failureBrakeThickness",
        "currentBrakeThickness",
        "lastLapBrakeWear",
        "estimatedBrakeWear",
        "estimatedValidBrakeWear",
    )

    def __init__(self):
        self.lockingPercentFront: float = 0.0
        self.lockingPercentRear: float = 0.0
        self.corneringRadius: float = 0.0
        self.slipRatio: list[float] = list(WHEELS_ZERO)
        self.currentTreadDepth: list[float] = list(WHEELS_ZERO)
        self.lastLapTreadWear: list[float] = list(WHEELS_ZERO)
        self.estimatedTreadWear: list[float] = list(WHEELS_ZERO)
        self.estimatedValidTreadWear: list[float] = list(WHEELS_ZERO)
        self.maxBrakeThickness: list[float] = list(WHEELS_ZERO)
        self.failureBrakeThickness: list[float] = list(WHEELS_ZERO)
        self.currentBrakeThickness: list[float] = list(WHEELS_ZERO)
        self.lastLapBrakeWear: list[float] = list(WHEELS_ZERO)
        self.estimatedBrakeWear: list[float] = list(WHEELS_ZERO)
        self.estimatedValidBrakeWear: list[float] = list(WHEELS_ZERO)


class ModuleInfo:
    """Modules output data"""

    __slots__ = (
        "delta",
        "energy",
        "force",
        "fuel",
        "history",
        "hybrid",
        "mapping",
        "pacenotes",
        "relative",
        "sectors",
        "stats",
        "tracknotes",
        "vehicles",
        "wheels",
    )

    def __init__(self):
        self.delta = DeltaInfo()
        self.energy = FuelInfo()
        self.force = ForceInfo()
        self.fuel = FuelInfo()
        self.history = HistoryInfo()
        self.hybrid = HybridInfo()
        self.mapping = MappingInfo()
        self.pacenotes = NotesInfo()
        self.relative = RelativeInfo()
        self.sectors = SectorsInfo()
        self.stats = StatsInfo()
        self.tracknotes = NotesInfo()
        self.vehicles = VehiclesInfo()
        self.wheels = WheelsInfo()


minfo = ModuleInfo()
