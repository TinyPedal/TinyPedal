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
Module info
"""

from __future__ import annotations

from collections import deque
from typing import KeysView, Mapping, NamedTuple

from .calculation import circular_position_relative, linear_interp
from .const_common import (
    DELTA_DEFAULT,
    EMPTY_DICT,
    MAX_METERS,
    MAX_SECONDS,
    MAX_VEHICLES,
    REL_TIME_DEFAULT,
)
from .decorator import df_deque, df_list, df_tuple, df_wrap, slotclass

# Class

class ConsumptionData(NamedTuple):
    """Consumption history data"""

    lapNumber: int = 0
    isValidLap: int = 0
    lapTimeLast: float = 0.0
    lastLapUsedFuel: float = 0.0
    lastLapUsedEnergy: float = 0.0
    batteryDrainLast: float = 0.0
    batteryRegenLast: float = 0.0
    tyreAvgWearLast: float = 0.0
    capacityFuel: float = 0.0


@slotclass
class MapCoords:
    """Map coords data

    Attributes:
        coords: x,y coordinates list.
        dists: distance,elevation list.
        sectors: sector node index reference list.
    """

    coords: tuple[tuple[float, float], ...] = ()
    dists: tuple[tuple[float, float], ...] = ()
    sectors: tuple[int, ...] = ()

    def is_valid(self) -> bool:
        """Is valid data"""
        return all((self.coords, self.dists, self.sectors))

    def clear(self):
        """Clear coords data"""
        self.__init__()

    def new(self):
        """Set new coords data"""
        self.coords = []
        self.dists = []
        self.sectors = [0, 0]


@slotclass
class DriverStats:
    """Driver stats data

    Attributes:
        pb: personal best lap time.
        qb: qualifying best lap time.
        rb: race best lap time.
        meters: meters driven.
        seconds: seconds spent driving.
        liters: liters of fuel consumed.
        valid: valid laps.
        invalid: invalid laps.
        penalties: penalties recieved in race.
        races: number of races completed.
        wins: number of wins.
        podiums: number of podiums.
    """

    pb: float = MAX_SECONDS
    qb: float = MAX_SECONDS
    rb: float = MAX_SECONDS
    meters: float = 0.0
    seconds: float = 0.0
    liters: float = 0.0
    valid: int = 0
    invalid: int = 0
    penalties: int = 0
    races: int = 0
    wins: int = 0
    podiums: int = 0

    def reset(self):
        """Reset"""
        self.__init__()

    @classmethod
    def keys(cls) -> KeysView[str]:
        """Get key name list"""
        return cls.__annotations__.keys()

    @staticmethod
    def is_lap_time(key: str) -> bool:
        """Is lap time"""
        return key in ("pb", "qb", "rb")

    def update(self, data: dict) -> None:
        """Update with new values"""
        for key in self.__annotations__:
            new_value = data.get(key)
            if new_value is not None:
                setattr(self, key, new_value)

    def output(self) -> dict:
        """Output data as dict"""
        return {k: getattr(self, k) for k in self.__annotations__}


@slotclass
class StintData:
    """Stint data"""

    totalLaps: int = 0
    totalTime: float = 0
    totalFuel: float = 0.0
    totalEnergy: float = 0.0
    totalTyreWear: float = 0.0
    lapTimeDelta: float = 0.0
    lapTimeConsistency: float = 0.0
    tyreCompound: str = "----"

    def reset(self):
        """Reset"""
        self.__init__()

    def copy(self) -> StintData:
        """Create a copy of this stint data"""
        new_data = StintData()
        for key in self.__annotations__:
            setattr(new_data, key, getattr(self, key))
        return new_data


@slotclass
class DeltaTimeInterval:
    """Delta time interval data

    Attributes:
        last: Last time interval.
        long: Average time interval (long duration).
        normal: Average time interval (normal duration).
        short: Average time interval (short duration).
    """

    last: float = 0.0
    long: float = 0.0
    normal: float = 0.0
    short: float = 0.0

    def update(self, time_interval: float):
        """Update delta time interval"""
        if self.last != time_interval:
            diff = self.last - time_interval
            if abs(diff) < 3:  # position switch check
                self.long += 0.01 * (diff - self.long)  # 200s
                self.normal += 0.02 * (diff - self.normal)  # 100s
                self.short += 0.065 * (diff - self.short)  # 30s
                # Sync longer duration with short if higher than 0.3 difference
                if abs(self.normal - self.short) > 0.3:
                    self.normal = self.short
                if abs(self.long - self.normal) > 0.3:
                    self.long = self.normal
            self.last = time_interval


@slotclass
class DeltaLapTimeHistory:
    """Delta lap time history data

    Attributes:
        data: Lap time array.
        start: Last updated lap start timestamp.
        best: Best lap time from recent laps.
        last: Last lap time, can be invalid.
        average: Average lap time from recent laps.
    """

    data: list[float] = df_list(0.0, 5)
    start: float = 0.0
    best: float = 0.0
    last: float = 0.0
    average: float = 0.0

    def update(self, lap_start: float, elapsed_time: float, best_valid: float):
        """Update delta lap time history"""
        if self.start != lap_start and elapsed_time - lap_start > 1:
            data = self.data
            if 0 < self.start < lap_start:
                data[0], data[1], data[2], data[3] = data[1], data[2], data[3], data[4]
                data[4] = lap_start - self.start  # last lap time
            else:  # reset all laptime on session change
                data[0] = data[1] = data[2] = data[3] = data[4] = 0.0
            self.start = lap_start
            # Recalculate once per lap
            if best_valid <= 0:
                best_recent = MAX_SECONDS
            else:
                # Find best time from recent laps
                best_recent = min(self._filter_laptime(best_valid))
                if best_recent >= MAX_SECONDS:  # fallback to session best
                    best_recent = best_valid
            self.best = best_recent
            self.average = self._average_laptime(self.best)
            self.last = data[4]

    def _average_laptime(self, laptime_best: float) -> float:
        """Calculate average lap time"""
        if laptime_best >= MAX_SECONDS:
            return MAX_SECONDS
        laptime_sum = 0
        count = 0
        margin = laptime_best * 1.2
        for laptime in self._filter_laptime(laptime_best):
            # Make sure lap time within 120% of recent best laptime
            if laptime <= margin:
                laptime_sum += laptime
                count += 1
        if count:
            return laptime_sum / count
        return laptime_best

    def _filter_laptime(self, best_valid: float):
        """Filter invalid lap time"""
        best_valid -= 0.01  # compensate precision
        for laptime in self.data:
            # Make sure lap time is not lower than session best valid lap time
            if laptime >= best_valid > 0:
                yield laptime
            else:
                yield MAX_SECONDS


@slotclass
class DeltaFuelHistory:
    """Delta fuel history data

    Attributes:
        used: Last lap used fuel.
        laps: Last lap remaining laps.
    """

    _last_lap_start: float = 0.0
    _last_remaining: float = 0.0
    used: float = 0.0
    laps: float = 0.0

    def update(self, lap_start: float, remaining: float):
        """Update delta lap time history"""
        if self._last_lap_start != lap_start:
            if 0 < self._last_lap_start < lap_start:
                if self._last_remaining > remaining:
                    self.used = self._last_remaining - remaining
                self._last_remaining = remaining
                if self.used > 0:
                    self.laps = remaining / self.used
            else:  # reset all laptime on session change
                self.used = self.laps = self._last_remaining = 0.0
            self._last_lap_start = lap_start


@slotclass
class LicoTimer:
    """Lift and coast timer

    Attributes:
        idling: time since last lico.
        elapsed: last recorded lico time.
    """

    _last_time: float = 0.0
    _cooldown_time: float = 0.0
    _warmup_time: float = 0.0
    idling: float = 0.0
    elapsed: float = 0.0

    def update(self, elapsed_time: float, throttle_raw: float, brake_raw: float):
        """Update lico timer"""
        braking = brake_raw > 0.01
        delta_time = elapsed_time - self._last_time
        self._last_time = elapsed_time
        if delta_time < 0:
            delta_time = 0
        # Always reset on braking
        if braking:
            self._cooldown_time = 0
        # Count 3s continuous throttling
        elif self._cooldown_time < 3:
            if throttle_raw >= 0.8:  # workaround network inaccuracy
                self._cooldown_time += delta_time
            else:  # reset if released early
                self._cooldown_time = 0
        # Lift and coasting
        if self._cooldown_time >= 3 and not braking and throttle_raw < 0.1:
            if self._warmup_time < 0.5:  # ignore auto-lift from upshifting
                self._warmup_time += delta_time
            else:
                if self.idling:  # reset
                    self.elapsed = self._warmup_time
                    self.idling = 0
                self.elapsed += delta_time
        else:
            if not self.idling:
                self._cooldown_time = 0
            self.idling += delta_time
            self._warmup_time = 0


@slotclass
class SpeedTrap:
    """Speed trap

    Attributes:
        speed: Speed(m/s) at speed trap.
    """

    _record_next: bool = False
    _speed_before: float = 0.0
    _distance_last: float = 0.0
    _distance_before: float = 0.0
    speed: float = 0.0

    def update(self, speed: float, distance_into: float, speedtrap_distance: float, track_length: float):
        """Update speed trap data"""
        if self._distance_last == distance_into:
            return
        self._distance_last = distance_into

        # Center distance to speed trap position
        distance_into = circular_position_relative(track_length, speedtrap_distance, distance_into)

        if self._record_next:
            # Distance before speed trap
            if 0 > distance_into:
                self._distance_before = distance_into
                self._speed_before = speed
            else:
                # Distance after speed trap
                if distance_into - self._distance_before < 200:
                    self.speed = linear_interp(
                        0,
                        self._distance_before,
                        self._speed_before,
                        distance_into,
                        speed,
                    )
                # Turn off record until distance circles back
                self._record_next = False
        elif 0 > distance_into:
            self._record_next = True


@slotclass
class PitTimer:
    """Pit timer

    Attributes:
        elapsed: Total time spent in pit.
        stopped: Total time spent while stopped in pit.
        pitting: Is pitting in or out.
        laps: Total laps done since last pit stop.
    """

    _last_pit_lap: int = 99999
    _last_state: int = 0
    _pitin_time: float = 0.0
    _pitstop_time: float = 0.0
    elapsed: float = 0.0
    stopped: float = 0.0
    pitting: bool = False
    laps: int = 0

    def update(self, in_pit: int, elapsed_time: float, laps_done: int, speed: float):
        """Calculate pit time

        Pit state: 0 = not in pit, 1 = in pit, 2 = in garage.
        """
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
        self.laps = laps_done - self._last_pit_lap


@slotclass
class VehicleDataSet:
    """Vehicle data set"""

    isPlayer: bool = False
    elapsedTime: float = 0.0
    speed: float = 0.0
    positionOverall: int = 0
    positionInClass: int = 0
    qualifyOverall: int = 0
    qualifyInClass: int = 0
    driverName: str = ""
    vehicleName: str = ""
    vehicleBrand: str = ""
    vehicleClass: str = ""
    classAheadIndex: int = -1
    classBehindIndex: int = -1
    classLeaderIndex: int = -1
    classBestLapTime: float = MAX_SECONDS
    bestLapTime: float = MAX_SECONDS
    lastLapTime: float = MAX_SECONDS
    currentLapProgress: float = 0.0
    totalLapProgress: float = 0.0
    gapBehindNext: float = 0.0
    gapBehindNextInClass: float = 0.0
    gapBehindLeader: float = 0.0
    gapBehindLeaderInClass: float = 0.0
    isLapped: float = 0.0
    isYellow: bool = False
    isValidLap: bool = False
    isFinished: bool = False
    inPit: int = 0
    isClassFastestLastLap: bool = False
    numPitStops: int = 0
    pitRequested: bool = False
    tireCompoundName: tuple[str, ...] = ("", "", "", "")
    relativeOrientationRadians: float = 0.0
    relativeStraightDistance: float = 0.0
    worldPositionX: float = 0.0
    worldPositionY: float = 0.0
    relativeRotatedPositionX: float = 0.0
    relativeRotatedPositionY: float = 0.0
    vehicleIntegrity: float = 0.0
    incidents: int = 0
    energyRemaining: float = 0.0
    estimatedStintLaps: float = 0.0
    currentStintLaps: int = 0
    licoTimer: LicoTimer = df_wrap(LicoTimer)
    pitTimer: PitTimer = df_wrap(PitTimer)
    speedTrap: SpeedTrap = df_wrap(SpeedTrap)
    fuelHistory: DeltaFuelHistory = df_wrap(DeltaFuelHistory)
    energyHistory: DeltaFuelHistory = df_wrap(DeltaFuelHistory)
    lapTimeHistory: DeltaLapTimeHistory = df_wrap(DeltaLapTimeHistory)


@slotclass
class DeltaInfo:
    """Delta output data"""

    deltaBestData: tuple[tuple[float, float], ...] = DELTA_DEFAULT
    deltaBest: float = 0.0
    deltaLast: float = 0.0
    deltaSession: float = 0.0
    deltaStint: float = 0.0
    isValidLap: bool = False
    lapTimeCurrent: float = 0.0
    lapTimeLast: float = 0.0
    lapTimeBest: float = 0.0
    lapTimeEstimated: float = 0.0
    lapTimeSession: float = 0.0
    lapTimeStint: float = 0.0
    lapTimePace: float = 0.0
    lapDistance: float = 0.0


@slotclass
class ForceInfo:
    """Force output data"""

    lgtGForceRaw: float = 0.0
    latGForceRaw: float = 0.0
    maxAvgLatGForce: float = 0.0
    maxLgtGForce: float = 0.0
    maxLatGForce: float = 0.0
    downForceFront: float = 0.0
    downForceRear: float = 0.0
    downForceRatio: float = 0.0
    brakingRate: float = 0.0
    transientMaxBrakingRate: float = 0.0
    maxBrakingRate: float = 0.0
    deltaBrakingRate: float = 0.0


@slotclass
class FuelInfo:
    """Fuel output data"""

    available: bool = False
    capacity: float = 0.0
    amountStart: float = 0.0
    amountCurrent: float = 0.0
    amountUsedCurrent: float = 0.0
    amountEndStint: float = 0.0
    neededRelative: float = 0.0
    neededAbsolute: float = 0.0
    lastLapConsumption: float = 0.0
    estimatedConsumption: float = 0.0
    estimatedValidConsumption: float = 0.0
    estimatedLaps: float = 0.0
    estimatedMinutes: float = 0.0
    estimatedNumPitStopsEnd: float = 0.0
    estimatedNumPitStopsEarly: float = 0.0
    deltaConsumption: float = 0.0
    oneLessPitConsumption: float = 0.0
    rateOfConsumption: float = 0.0
    weight: float = 0.0

    def reset(self):
        """Reset"""
        self.__init__()


@slotclass
class HistoryInfo:
    """History output data"""

    consumptionDataVersion: int = 0
    consumptionDataSet: deque[ConsumptionData] = df_deque(ConsumptionData, 100)
    stintDataVersion: int = 0
    stintDataCurrent: StintData = df_wrap(StintData)
    stintDataSet: deque[StintData] = df_deque(StintData, 100)

    def reset_stint(self):
        """Reset stint data"""
        self.stintDataVersion = 0
        self.stintDataCurrent.reset()
        self.stintDataSet.clear()
        self.stintDataSet.appendleft(StintData())


@slotclass
class HybridInfo:
    """Hybrid output data"""

    batteryCharge: float = 0.0
    batteryDrain: float = 0.0
    batteryRegen: float = 0.0
    batteryDrainLast: float = 0.0
    batteryRegenLast: float = 0.0
    batteryNetChange: float = 0.0
    motorActiveTimer: float = 0.0
    motorInactiveTimer: float = 0.0
    motorState: int = 0
    fuelEnergyRatio: float = 0.0
    fuelEnergyBias: float = 0.0


@slotclass
class MappingInfo:
    """Mapping output data"""

    # Map data
    coordinates: tuple[tuple[float, float], ...] = ()
    elevations: tuple[tuple[float, float], ...] = ()
    sectors: tuple[int, ...] = ()
    lastModified: float = 0.0
    # Track info
    speedTrapPosition: float = 0.0
    pitEntryPosition: float = 0.0
    pitExitPosition: float = 0.0
    pitLaneLength: float = 0.0
    pitSpeedLimit: float = 0.0
    pitPassTime: float = 0.0
    sunlightPhases: tuple[tuple[float, int], ...] = ()

    def reset(self):
        """Reset"""
        self.__init__()


@slotclass
class NotesData:
    """Notes data

    Attributes:
        currentIndex: notes index.
        currentNote: notes data[notes column name, value].
        nextIndex: notes index.
        nextNote: notes data[notes column name, value].
    """

    currentIndex: int = 0
    currentNote: Mapping[str, float | str] = EMPTY_DICT
    nextIndex: int = 0
    nextNote: Mapping[str, float | str] = EMPTY_DICT

    def reset(self):
        """Reset"""
        self.__init__()


@slotclass
class NotesInfo:
    """Notes output data"""

    out: NotesData = df_wrap(NotesData)
    pit: NotesData = df_wrap(NotesData)


@slotclass
class RelativeInfo:
    """Relative output data"""

    relativeAhead: list[tuple[float, int]] = df_list(REL_TIME_DEFAULT)
    relativeBehind: list[tuple[float, int]] = df_list(REL_TIME_DEFAULT)
    standings: list[int] = df_list(-1)
    drawOrder: list[int] = df_list(0)
    relativeDeltaAhead: tuple[DeltaTimeInterval, ...] = df_tuple(DeltaTimeInterval, MAX_VEHICLES)
    relativeDeltaBehind: tuple[DeltaTimeInterval, ...] = df_tuple(DeltaTimeInterval, MAX_VEHICLES)


@slotclass
class SectorData:
    """Sector data set"""

    noDeltaSector: bool = True
    sectorIndex: int = -1
    sectorPrev: list[float] = df_list(MAX_SECONDS, 3)
    sectorBestTB: list[float] = df_list(MAX_SECONDS, 3)
    sectorBestPB: list[float] = df_list(MAX_SECONDS, 3)
    deltaSectorBestPB: list[float] = df_list(0.0, 3)
    deltaSectorBestTB: list[float] = df_list(0.0, 3)

    def reset(self):
        """Reset"""
        self.__init__()


@slotclass
class SectorsInfo:
    """Sectors output data"""

    allTimeBest: SectorData = df_wrap(SectorData)
    sessionBest: SectorData = df_wrap(SectorData)


@slotclass
class StatsInfo:
    """Stats output data"""

    metersDriven: float = 0.0


@slotclass
class VehiclesInfo:
    """Vehicles output data"""

    dataSet: tuple[VehicleDataSet, ...] = df_tuple(VehicleDataSet, MAX_VEHICLES)
    dataSetVersion: int = -1
    leaderIndex: int = 0
    playerIndex: int = -1
    totalOutPits: int = 0
    totalInPits: int = 0
    totalStoppedPits: int = 0
    totalPitRequests: int = 0
    totalCompletedLaps: int = 0
    totalVehicles: int = 0
    nearestLine: float = MAX_METERS
    nearestTraffic: float = MAX_SECONDS
    nearestYellowAhead: float = MAX_METERS
    nearestYellowBehind: float = -MAX_METERS
    nearestBlueClass: str = ""
    leaderBestLapTime: float = MAX_SECONDS
    finishTimeOffset: float = 0.0
    finishAsLap: bool = True
    finishLapOffset: float = 0.0


@slotclass
class WheelsInfo:
    """Wheels output data"""

    # Rotation
    lockingPercentFront: float = 0.0
    lockingPercentRear: float = 0.0
    lockingTime: list[float] = df_list(0.0, 4)
    yawRate: float = 0.0
    # Tyre wear
    currentTreadDepth: list[float] = df_list(0.0, 4)
    currentLapTreadWear: list[float] = df_list(0.0, 4)
    lastLapTreadWear: list[float] = df_list(0.0, 4)
    estimatedTreadWear: list[float] = df_list(0.0, 4)
    estimatedValidTreadWear: list[float] = df_list(0.0, 4)
    lockingTreadWear: list[float] = df_list(0.0, 4)
    # Brake wear
    maxBrakeThickness: list[float] = df_list(0.0, 4)
    failureBrakeThickness: list[float] = df_list(0.0, 4)
    currentBrakeThickness: list[float] = df_list(0.0, 4)
    currentlapBrakeWear: list[float] = df_list(0.0, 4)
    lastLapBrakeWear: list[float] = df_list(0.0, 4)
    estimatedBrakeWear: list[float] = df_list(0.0, 4)
    estimatedValidBrakeWear: list[float] = df_list(0.0, 4)
    # Suspension
    currentSuspensionPosition: list[float] = df_list(0.0, 4)
    staticSuspensionPosition: list[float] = df_list(0.0, 4)
    minSuspensionPosition: list[float] = df_list(0.0, 4)
    maxSuspensionPosition: list[float] = df_list(0.0, 4)
    motionRatio: list[float] = df_list(0.0, 4)
    # Weight
    minimumStaticWeight: float = 0.0
    totalStaticWeight: float = 0.0
    totalDynamicWeight: float = 0.0
    frontWeightRatio: float = 0.0
    leftWeightRatio: float = 0.0
    crossWeightRatio: float = 0.0
    # Slip ratio
    slipRatio: list[float] = df_list(0.0, 4)
    # Slip angle
    slipAngle: list[float] = df_list(0.0, 4)
    averageFrontSlipAngle: float = 0.0
    averageRearSlipAngle: float = 0.0
    slipAngleDifference: float = 0.0
    # Toe angle
    toeAngle: list[float] = df_list(0.0, 4)
    averageFrontToeAngle: float = 0.0
    averageRearToeAngle: float = 0.0
    frontToeAngleDifference: float = 0.0
    rearToeAngleDifference: float = 0.0
    # Camber angle
    camberAngle: list[float] = df_list(0.0, 4)
    frontCamberAngleDifference: float = 0.0
    rearCamberAngleDifference: float = 0.0


@slotclass
class ModuleInfo:
    """Modules output data"""

    delta: DeltaInfo = df_wrap(DeltaInfo)
    energy: FuelInfo = df_wrap(FuelInfo)
    force: ForceInfo = df_wrap(ForceInfo)
    fuel: FuelInfo = df_wrap(FuelInfo)
    history: HistoryInfo = df_wrap(HistoryInfo)
    hybrid: HybridInfo = df_wrap(HybridInfo)
    mapping: MappingInfo = df_wrap(MappingInfo)
    relative: RelativeInfo = df_wrap(RelativeInfo)
    sectors: SectorsInfo = df_wrap(SectorsInfo)
    stats: StatsInfo = df_wrap(StatsInfo)
    pacenotes: NotesInfo = df_wrap(NotesInfo)
    tracknotes: NotesInfo = df_wrap(NotesInfo)
    vehicles: VehiclesInfo = df_wrap(VehiclesInfo)
    wheels: WheelsInfo = df_wrap(WheelsInfo)


minfo = ModuleInfo()
