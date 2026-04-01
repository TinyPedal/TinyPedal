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
LMU API data reader

Notes:
    Convert all temperature (kelvin) to Celsius before output.
"""

from __future__ import annotations

from ..calculation import (
    lap_progress_distance,
    mean,
    min_nonzero,
    oriyaw2rad,
    slip_angle,
    vel2speed,
)
from ..const_common import MAX_SECONDS, STINT_USAGE_DEFAULT
from ..formatter import strip_invalid_char
from ..process.weather import WeatherNode
from ..validator import bytes_to_str as tostr
from ..validator import infnan_to_zero as rmnan
from . import _reader
from .lmu_connector import LMU_COMPOUND_TYPE, LMUInfo
from .lmu_restapi import RestAPIData


class DataAdapter:
    """Read & sort data into groups"""

    __slots__ = (
        "shmm",
        "rest",
    )

    def __init__(self, shmm: LMUInfo, rest: RestAPIData) -> None:
        """Initialize API setting

        Args:
            shmm: shared memory API connector.
            rest: rest API connector.
        """
        self.shmm = shmm
        self.rest = rest


class State(_reader.State, DataAdapter):
    """State"""

    __slots__ = ()

    def active(self) -> bool:
        """Is active (driving or overriding)"""
        return self.shmm.isActive

    def paused(self) -> bool:
        """Is paused"""
        return self.shmm.isPaused

    def desynced(self, index: int | None = None) -> bool:
        """Is player data desynced from others"""
        return (
            abs(self.shmm.lmuTeleVeh().mElapsedTime
            - self.shmm.lmuTeleVeh(index).mElapsedTime)
            >= 0.01
        )

    def version(self) -> str:
        """Identify API version"""
        version = str(self.shmm.lmuGeneric.gameVersion)
        if len(version) < 2:
            return "unknown"
        return f"{version[0]}.{version[1:]}"


class Brake(_reader.Brake, DataAdapter):
    """Brake"""

    __slots__ = ()

    def bias_front(self, index: int | None = None) -> float:
        """Brake bias front (fraction)"""
        return 1 - rmnan(self.shmm.lmuTeleVeh(index).mRearBrakeBias)

    def migration(self, index: int | None = None) -> float:
        """Brake migration (percent)"""
        tele_veh = self.shmm.lmuTeleVeh(index)
        max_migration = tele_veh.mMigrationMax
        if max_migration > 0:
            return rmnan(1 - tele_veh.mMigration / max_migration) * 2.5
        return 0.0

    def pressure(self, index: int | None = None, scale: float = 1) -> tuple[float, ...]:
        """Brake pressure (fraction)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mBrakePressure) * scale,
            rmnan(wheel_data[1].mBrakePressure) * scale,
            rmnan(wheel_data[2].mBrakePressure) * scale,
            rmnan(wheel_data[3].mBrakePressure) * scale,
        )

    def temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Brake temperature (Celsius)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mBrakeTemp) - 273.15,
            rmnan(wheel_data[1].mBrakeTemp) - 273.15,
            rmnan(wheel_data[2].mBrakeTemp) - 273.15,
            rmnan(wheel_data[3].mBrakeTemp) - 273.15,
        )

    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Brake remaining thickness (meters)"""
        return self.rest.brakeWear


class ElectricMotor(_reader.ElectricMotor, DataAdapter):
    """Electric motor"""

    __slots__ = ()

    def state(self, index: int | None = None) -> int:
        """Motor state, 0 = n/a, 1 = off, 2 = drain, 3 = regen"""
        state = self.shmm.lmuTeleVeh(index).mElectricBoostMotorState
        if state == 0:
            return 0
        if state == 1:
            return 1
        if state == 2:
            return 2
        if state == 3:
            return 3
        return 0

    def battery_charge(self, index: int | None = None) -> float:
        """Battery charge (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mBatteryChargeFraction)

    def rpm(self, index: int | None = None) -> float:
        """Motor RPM (rev per minute)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mElectricBoostMotorRPM)

    def torque(self, index: int | None = None) -> float:
        """Motor torque (Nm)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mElectricBoostMotorTorque)

    def motor_temperature(self, index: int | None = None) -> float:
        """Motor temperature (Celsius)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mElectricBoostMotorTemperature)

    def water_temperature(self, index: int | None = None) -> float:
        """Motor water temperature (Celsius)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mElectricBoostWaterTemperature)

    def regeneration_level(self, index: int | None = None) -> float:
        """Regeneration level (kW)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mRegen)


class Engine(_reader.Engine, DataAdapter):
    """Engine"""

    __slots__ = ()

    def gear(self, index: int | None = None) -> int:
        """Gear"""
        return self.shmm.lmuTeleVeh(index).mGear

    def gear_max(self, index: int | None = None) -> int:
        """Max gear"""
        return self.shmm.lmuTeleVeh(index).mMaxGears

    def rpm(self, index: int | None = None) -> float:
        """RPM (rev per minute)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mEngineRPM)

    def rpm_max(self, index: int | None = None) -> float:
        """Max RPM (rev per minute)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mEngineMaxRPM)

    def torque(self, index: int | None = None) -> float:
        """Torque (Nm)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mEngineTorque)

    def turbo(self, index: int | None = None) -> float:
        """Turbo pressure (Pa)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mTurboBoostPressure)

    def oil_temperature(self, index: int | None = None) -> float:
        """Oil temperature (Celsius)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mEngineOilTemp)

    def water_temperature(self, index: int | None = None) -> float:
        """Water temperature (Celsius)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mEngineWaterTemp)

    def lift_and_coast_progress(self, index: int | None = None) -> float:
        """Lift and coast progress (fraction), range 0.0 to 1.0"""
        return self.shmm.lmuTeleVeh(index).mLiftAndCoastProgress / 255


class Inputs(_reader.Inputs, DataAdapter):
    """Inputs"""

    __slots__ = ()

    def throttle(self, index: int | None = None) -> float:
        """Throttle filtered (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mFilteredThrottle)

    def throttle_raw(self, index: int | None = None) -> float:
        """Throttle raw (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mUnfilteredThrottle)

    def brake(self, index: int | None = None) -> float:
        """Brake filtered (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mFilteredBrake)

    def brake_raw(self, index: int | None = None) -> float:
        """Brake raw (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mUnfilteredBrake)

    def clutch(self, index: int | None = None) -> float:
        """Clutch filtered (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mFilteredClutch)

    def clutch_raw(self, index: int | None = None) -> float:
        """Clutch raw (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mUnfilteredClutch)

    def steering(self, index: int | None = None) -> float:
        """Steering filtered (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mFilteredSteering)

    def steering_raw(self, index: int | None = None) -> float:
        """Steering raw (fraction)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mUnfilteredSteering)

    def steering_shaft_torque(self, index: int | None = None) -> float:
        """Steering shaft torque (Nm)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mSteeringShaftTorque)

    def steering_range_physical(self, index: int | None = None) -> float:
        """Steering physical rotation range (degrees)"""
        rot_range = rmnan(self.shmm.lmuTeleVeh(index).mPhysicalSteeringWheelRange)
        if rot_range <= 0:
            rot_range = self.rest.steeringWheelRange
        return rot_range

    def steering_range_visual(self, index: int | None = None) -> float:
        """Steering visual rotation range (degrees)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mVisualSteeringWheelRange)

    def force_feedback(self) -> float:
        """Steering force feedback (fraction)"""
        return rmnan(self.shmm.lmuGeneric.FFBTorque)


class Lap(_reader.Lap, DataAdapter):
    """Lap"""

    __slots__ = ()

    def number(self, index: int | None = None) -> int:
        """Current lap number"""
        return self.shmm.lmuTeleVeh(index).mLapNumber

    def completed_laps(self, index: int | None = None) -> int:
        """Total completed laps"""
        return self.shmm.lmuScorVeh(index).mTotalLaps

    def track_length(self) -> float:
        """Full lap or track length (meters)"""
        return rmnan(self.shmm.lmuScorInfo.mLapDist)

    def distance(self, index: int | None = None) -> float:
        """Distance into lap (meters)"""
        return rmnan(self.shmm.lmuScorVeh(index).mLapDist)

    def progress(self, index: int | None = None) -> float:
        """Lap progress (fraction), distance into lap"""
        return rmnan(lap_progress_distance(
            self.shmm.lmuScorVeh(index).mLapDist,
            self.shmm.lmuScorInfo.mLapDist))

    def maximum(self) -> int:
        """Maximum lap"""
        return self.shmm.lmuScorInfo.mMaxLaps

    def remaining(self, index: int | None = None) -> float:
        """Remaining lap, count from current lap progress"""
        scor = self.shmm.lmuScorInfo
        scor_veh = self.shmm.lmuScorVeh(index)
        progress = lap_progress_distance(scor_veh.mLapDist, scor.mLapDist)
        return rmnan(scor.mMaxLaps - scor_veh.mTotalLaps - progress)

    def sector_index(self, index: int | None = None) -> int:
        """Sector index, 0 = S1, 1 = S2, 2 = S3"""
        # LMU sector index 0 = S3, index 1 = S1, index 2 = S2
        sector = self.shmm.lmuScorVeh(index).mSector
        if sector == 0:
            return 2
        if sector == 1:
            return 0
        return 1

    def behind_leader(self, index: int | None = None) -> int:
        """Laps behind leader"""
        return self.shmm.lmuScorVeh(index).mLapsBehindLeader

    def behind_next(self, index: int | None = None) -> int:
        """Laps behind next place"""
        return self.shmm.lmuScorVeh(index).mLapsBehindNext

    def safety_car_distance(self) -> float:
        """Safety car's distance into lap (meters)"""
        return 0.0  # not available for LMU

    def safety_car_active(self) -> bool:
        """Is safety car active on track"""
        return False  # not available for LMU


class Session(_reader.Session, DataAdapter):
    """Session"""

    __slots__ = ()

    def combo_name(self) -> str:
        """Track & vehicle combo name, strip off invalid char"""
        track_name = tostr(self.shmm.lmuScorInfo.mTrackName)
        class_name = tostr(self.shmm.lmuScorVeh().mVehicleClass)
        return strip_invalid_char(f"{track_name} - {class_name}")

    def track_name(self) -> str:
        """Track name, strip off invalid char"""
        return strip_invalid_char(tostr(self.shmm.lmuScorInfo.mTrackName))

    def identifier(self) -> tuple[int, int, int]:
        """Identify session"""
        session_length = rmnan(self.shmm.lmuScorInfo.mEndET)
        session_type = self.shmm.lmuScorInfo.mSession
        session_stamp = int(session_length * 100 + session_type)
        session_etime = int(rmnan(self.shmm.lmuScorInfo.mCurrentET))
        session_tlaps = self.shmm.lmuScorVeh().mTotalLaps
        return session_stamp, session_etime, session_tlaps

    def elapsed(self) -> float:
        """Session elapsed time (seconds)"""
        return rmnan(self.shmm.lmuScorInfo.mCurrentET)

    def start(self) -> float:
        """Session start time (seconds)"""
        return rmnan(self.shmm.lmuScorInfo.mStartET)

    def end(self) -> float:
        """Session end time (seconds)"""
        return rmnan(self.shmm.lmuScorInfo.mEndET)

    def remaining(self) -> float:
        """Session time remaining (seconds), minimum limit to 0"""
        scor = self.shmm.lmuScorInfo
        seconds = rmnan(scor.mEndET - scor.mCurrentET)
        if seconds < 0:
            seconds = 0.0
        return seconds

    def session_type(self) -> int:
        """Session type, 0 = TESTDAY, 1 = PRACTICE, 2 = QUALIFY, 3 = WARMUP, 4 = RACE"""
        session = self.shmm.lmuScorInfo.mSession
        if session >= 10:  # race
            return 4
        if session == 9:  # warmup
            return 3
        if session >= 5:  # qualify
            return 2
        if session >= 1:  # practice
            return 1
        return 0  # test day

    def finish_type(self, as_lap: bool | None = None) -> int:
        """Race finish type, 0 = time, 1 = laps only, 2 = laps & time"""
        scor = self.shmm.lmuScorInfo
        if scor.mMaxLaps > 999999:
            return 0  # time only
        if as_lap is not None:
            return as_lap  # override
        if scor.mEndET < 1:
            return 1  # laps only
        return 2  # laps & time

    def in_race(self) -> bool:
        """Is in race session"""
        return self.shmm.lmuScorInfo.mSession > 9

    def private_qualifying(self) -> bool:
        """Is private qualifying"""
        return self.rest.privateQualifying == 1

    def pit_open(self) -> bool:
        """Is pit lane open"""
        return self.shmm.lmuScorInfo.mGamePhase > 0

    def pre_race(self) -> bool:
        """Before race starts (green flag)"""
        return self.shmm.lmuScorInfo.mGamePhase <= 4

    def green_flag(self) -> bool:
        """Green flag (race starts)"""
        # Inaccurate due to 5FPS refresh rate from API
        return self.shmm.lmuScorInfo.mGamePhase == 5

    def blue_flag(self, index: int | None = None) -> bool:
        """Is under blue flag"""
        return self.shmm.lmuScorVeh(index).mFlag == 6

    def yellow_flag(self) -> bool:
        """Is there yellow flag in any sectors"""
        sec_flag = self.shmm.lmuScorInfo.mSectorFlag
        return any(data == 1 for data in sec_flag)

    def start_lights(self) -> int:
        """Start lights countdown sequence, 0=green flag"""
        scor = self.shmm.lmuScorInfo
        # Green flag check
        if scor.mGamePhase >= 5:  # inaccurate (5fps refresh rate from API)
            return 0
        # Workaround for accurate green flag moment (standing-start type only)
        tele_data = self.shmm.lmuTeleVeh()
        if tele_data.mElapsedTime - tele_data.mLapStartET >= 0:
            return 0
        # Start lights sequence
        return scor.mNumRedLights - scor.mStartLight + 1

    def track_temperature(self) -> float:
        """Track temperature (Celsius)"""
        return rmnan(self.shmm.lmuScorInfo.mTrackTemp)

    def ambient_temperature(self) -> float:
        """Ambient temperature (Celsius)"""
        return rmnan(self.shmm.lmuScorInfo.mAmbientTemp)

    def raininess(self) -> float:
        """Rain severity (fraction), range 0.0 - 1.0

        Rain in percent:
            1-10 drizzle, 11-20 light rain, 21-40 rain, 41-60 heavy rain, 61-100 storm
        """
        return rmnan(self.shmm.lmuScorInfo.mRaining)

    def wetness_minimum(self) -> float:
        """Road minimum wetness (fraction)"""
        return rmnan(self.shmm.lmuScorInfo.mMinPathWetness)

    def wetness_maximum(self) -> float:
        """Road maximum wetness (fraction)"""
        return rmnan(self.shmm.lmuScorInfo.mMaxPathWetness)

    def wetness_average(self) -> float:
        """Road average wetness (fraction)"""
        return rmnan(self.shmm.lmuScorInfo.mAvgPathWetness)

    def wetness(self) -> tuple[float, float, float]:
        """Road wetness set (fraction)"""
        scor = self.shmm.lmuScorInfo
        return (rmnan(scor.mMinPathWetness),
                rmnan(scor.mMaxPathWetness),
                rmnan(scor.mAvgPathWetness))

    def weather_forecast(self) -> tuple[WeatherNode, ...]:
        """Weather forecast nodes"""
        session_type = self.session_type()
        if session_type <= 1:  # practice session
            return self.rest.forecastPractice
        if session_type == 2:  # qualify session
            return self.rest.forecastQualify
        return self.rest.forecastRace  # race session

    def cloud_coverage(self) -> int:
        """Cloud coverage (type index), range 0 to 10

        Sky type:
            0 Clear, 1 Light Clouds, 2 Partially Cloudy, 3 Mostly Cloudy, 4 Overcast,
            5 Cloudy & Drizzle, 6 Cloudy & Light Rain, 7 Overcast & Light Rain,
            8 Overcast & Rain, 9 Overcast & Heavy Rain, 10 Overcast & Storm
        """
        raininess = rmnan(self.shmm.lmuScorInfo.mRaining)
        if raininess <= 0:
            coverage = self.shmm.lmuScorInfo.mCloudCoverage
            if 0 >= coverage:
                return 0
            if 4 <= coverage:
                return 4
            return coverage
        if raininess <= 0.10:
            return 5
        if raininess <= 0.15:
            return 6
        if raininess <= 0.20:
            return 7
        if raininess <= 0.40:
            return 8
        if raininess <= 0.60:
            return 9
        return 10

    def track_time(self) -> float:
        """Track time"""
        return self.shmm.lmuScorInfo.mTimeOfDay

    def time_scale(self) -> int:
        """Time scale"""
        return max(self.rest.timeScale, 0)

    def limits_points(self) -> float:
        """Track limits points per penalty"""
        scor = self.shmm.lmuScorInfo
        points = scor.mTrackLimitsStepsPerPoint
        if points:
            return scor.mTrackLimitsStepsPerPenalty / points
        return 0.0

    def cut_points(self, index: int | None = None) -> float:
        """Current track limits cut points per penalty"""
        points = self.shmm.lmuScorInfo.mTrackLimitsStepsPerPoint
        if points:
            return self.shmm.lmuTeleVeh(index).mTrackLimitsSteps / points
        return 0.0


class Switch(_reader.Switch, DataAdapter):
    """Switch"""

    __slots__ = ()

    def headlights(self, index: int | None = None) -> int:
        """Headlights"""
        return self.shmm.lmuTeleVeh(index).mHeadlights

    def ignition_starter(self, index: int | None = None) -> int:
        """Ignition"""
        return self.shmm.lmuTeleVeh(index).mIgnitionStarter

    def speed_limiter(self, index: int | None = None) -> int:
        """Speed limiter"""
        return self.shmm.lmuTeleVeh(index).mSpeedLimiter

    def tc_active(self, index: int | None = None) -> bool:
        """TC activation state"""
        return self.shmm.lmuTeleVeh(index).mTCActive

    def abs_active(self, index: int | None = None) -> bool:
        """ABS activation state"""
        return self.shmm.lmuTeleVeh(index).mABSActive

    def drs_status(self, index: int | None = None) -> int:
        """DRS status, 0 not_available, 1 available, 2 allowed(not activated), 3 activated"""
        tele_veh = self.shmm.lmuTeleVeh(index)
        status = tele_veh.mRearFlapLegalStatus
        if status == 1:
            return 1  # available
        if status == 2:
            if tele_veh.mRearFlapActivated:
                return 3  # activated
            return 2  # allowed
        return 0  # not_available

    def auto_clutch(self) -> bool:
        """Auto clutch"""
        return False


class Timing(_reader.Timing, DataAdapter):
    """Timing"""

    __slots__ = ()

    def start(self, index: int | None = None) -> float:
        """Current lap start time (seconds)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLapStartET)

    def elapsed(self, index: int | None = None) -> float:
        """Current lap elapsed time (seconds)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mElapsedTime)

    def current_laptime(self, index: int | None = None) -> float:
        """Current lap time (seconds)"""
        tele_veh = self.shmm.lmuTeleVeh(index)
        return rmnan(tele_veh.mElapsedTime - tele_veh.mLapStartET)

    def last_laptime(self, index: int | None = None) -> float:
        """Last lap time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mLastLapTime)

    def best_laptime(self, index: int | None = None) -> float:
        """Best lap time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mBestLapTime)

    def reference_laptime(self, index: int | None = None, laptime: float = 0) -> float:
        """Reference lap time (seconds)"""
        if 0 < laptime < MAX_SECONDS:
            return laptime
        init_time = min_nonzero((
            self.best_laptime(index),
            self.last_laptime(index),
            MAX_SECONDS,
        ))
        if 0 < init_time < MAX_SECONDS:
            return init_time
        # Set to estimated laptime only if other laptime not available
        # as estimated laptime can be faster than other laptime
        return min_nonzero((
            self.estimated_laptime(index),
            MAX_SECONDS,
        ))

    def estimated_laptime(self, index: int | None = None) -> float:
        """Estimated lap time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mEstimatedLapTime)

    def estimated_time_into(self, index: int | None = None) -> float:
        """Estimated time into lap (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mTimeIntoLap)

    def current_sector1(self, index: int | None = None) -> float:
        """Current lap sector 1 time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mCurSector1)

    def current_sector2(self, index: int | None = None) -> float:
        """Current lap sector 1+2 time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mCurSector2)

    def last_sector1(self, index: int | None = None) -> float:
        """Last lap sector 1 time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mLastSector1)

    def last_sector2(self, index: int | None = None) -> float:
        """Last lap sector 1+2 time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mLastSector2)

    def best_sector1(self, index: int | None = None) -> float:
        """Best lap sector 1 time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mBestSector1)

    def best_sector2(self, index: int | None = None) -> float:
        """Best lap sector 1+2 time (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mBestSector2)

    def behind_leader(self, index: int | None = None) -> float:
        """Time behind leader (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mTimeBehindLeader)

    def behind_next(self, index: int | None = None) -> float:
        """Time behind next place (seconds)"""
        return rmnan(self.shmm.lmuScorVeh(index).mTimeBehindNext)


class Tyre(_reader.Tyre, DataAdapter):
    """Tyre (front left, front right, rear left, rear right)"""

    __slots__ = ()

    def compound_index(self, index: int | None = None) -> tuple[int, ...]:
        """Tyre compound index set"""
        tele_veh = self.shmm.lmuTeleVeh(index)
        front = tele_veh.mFrontTireCompoundIndex
        rear = tele_veh.mRearTireCompoundIndex
        return front, front, rear, rear

    def compound_name(self, index: int | None = None) -> tuple[str, ...]:
        """Tyre compound name set"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            LMU_COMPOUND_TYPE(wheel_data[0].mCompoundType),
            LMU_COMPOUND_TYPE(wheel_data[1].mCompoundType),
            LMU_COMPOUND_TYPE(wheel_data[2].mCompoundType),
            LMU_COMPOUND_TYPE(wheel_data[3].mCompoundType),
        )

    def compound_class(self, index: int | None = None) -> tuple[str, ...]:
        """Tyre compound name set with class name prefix"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        class_name = tostr(self.shmm.lmuScorVeh(index).mVehicleClass)
        return (
            f"{class_name} - {LMU_COMPOUND_TYPE(wheel_data[0].mCompoundType)}",
            f"{class_name} - {LMU_COMPOUND_TYPE(wheel_data[1].mCompoundType)}",
            f"{class_name} - {LMU_COMPOUND_TYPE(wheel_data[2].mCompoundType)}",
            f"{class_name} - {LMU_COMPOUND_TYPE(wheel_data[3].mCompoundType)}",
        )

    def surface_temperature_avg(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) average"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(mean(wheel_data[0].mTemperature)) - 273.15,
            rmnan(mean(wheel_data[1].mTemperature)) - 273.15,
            rmnan(mean(wheel_data[2].mTemperature)) - 273.15,
            rmnan(mean(wheel_data[3].mTemperature)) - 273.15,
        )

    def surface_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) inner,center,outer"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mTemperature[0]) - 273.15,
            rmnan(wheel_data[0].mTemperature[1]) - 273.15,
            rmnan(wheel_data[0].mTemperature[2]) - 273.15,
            rmnan(wheel_data[1].mTemperature[0]) - 273.15,
            rmnan(wheel_data[1].mTemperature[1]) - 273.15,
            rmnan(wheel_data[1].mTemperature[2]) - 273.15,
            rmnan(wheel_data[2].mTemperature[0]) - 273.15,
            rmnan(wheel_data[2].mTemperature[1]) - 273.15,
            rmnan(wheel_data[2].mTemperature[2]) - 273.15,
            rmnan(wheel_data[3].mTemperature[0]) - 273.15,
            rmnan(wheel_data[3].mTemperature[1]) - 273.15,
            rmnan(wheel_data[3].mTemperature[2]) - 273.15,
        )

    def inner_temperature_avg(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre inner temperature set (Celsius) average"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(mean(wheel_data[0].mTireInnerLayerTemperature)) - 273.15,
            rmnan(mean(wheel_data[1].mTireInnerLayerTemperature)) - 273.15,
            rmnan(mean(wheel_data[2].mTireInnerLayerTemperature)) - 273.15,
            rmnan(mean(wheel_data[3].mTireInnerLayerTemperature)) - 273.15,
        )

    def inner_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre inner temperature set (Celsius) inner,center,outer"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mTireInnerLayerTemperature[0]) - 273.15,
            rmnan(wheel_data[0].mTireInnerLayerTemperature[1]) - 273.15,
            rmnan(wheel_data[0].mTireInnerLayerTemperature[2]) - 273.15,
            rmnan(wheel_data[1].mTireInnerLayerTemperature[0]) - 273.15,
            rmnan(wheel_data[1].mTireInnerLayerTemperature[1]) - 273.15,
            rmnan(wheel_data[1].mTireInnerLayerTemperature[2]) - 273.15,
            rmnan(wheel_data[2].mTireInnerLayerTemperature[0]) - 273.15,
            rmnan(wheel_data[2].mTireInnerLayerTemperature[1]) - 273.15,
            rmnan(wheel_data[2].mTireInnerLayerTemperature[2]) - 273.15,
            rmnan(wheel_data[3].mTireInnerLayerTemperature[0]) - 273.15,
            rmnan(wheel_data[3].mTireInnerLayerTemperature[1]) - 273.15,
            rmnan(wheel_data[3].mTireInnerLayerTemperature[2]) - 273.15,
        )

    def pressure(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre pressure (kPa)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mPressure),
            rmnan(wheel_data[1].mPressure),
            rmnan(wheel_data[2].mPressure),
            rmnan(wheel_data[3].mPressure),
        )

    def load(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre load (Newtons)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mTireLoad),
            rmnan(wheel_data[1].mTireLoad),
            rmnan(wheel_data[2].mTireLoad),
            rmnan(wheel_data[3].mTireLoad),
        )

    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre wear (fraction)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mWear),
            rmnan(wheel_data[1].mWear),
            rmnan(wheel_data[2].mWear),
            rmnan(wheel_data[3].mWear),
        )

    def carcass_temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre carcass temperature (Celsius)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mTireCarcassTemperature) - 273.15,
            rmnan(wheel_data[1].mTireCarcassTemperature) - 273.15,
            rmnan(wheel_data[2].mTireCarcassTemperature) - 273.15,
            rmnan(wheel_data[3].mTireCarcassTemperature) - 273.15,
        )

    def vertical_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre vertical deflection (millimeters)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mVerticalTireDeflection) * 1000,
            rmnan(wheel_data[1].mVerticalTireDeflection) * 1000,
            rmnan(wheel_data[2].mVerticalTireDeflection) * 1000,
            rmnan(wheel_data[3].mVerticalTireDeflection) * 1000,
        )


class Vehicle(_reader.Vehicle, DataAdapter):
    """Vehicle"""

    __slots__ = ()

    def is_player(self, index: int=0) -> bool:
        """Is local player"""
        return self.shmm.playerIndex == index

    def is_driving(self) -> bool:
        """Is local player driving or in monitor"""
        return self.shmm.lmuTeleVeh().mIgnitionStarter > 0

    def player_index(self) -> int:
        """Get Local player index"""
        return self.shmm.playerIndex

    def slot_id(self, index: int | None = None) -> int:
        """Vehicle slot id"""
        return self.shmm.lmuScorVeh(index).mID

    def driver_name(self, index: int | None = None) -> str:
        """Driver name"""
        return tostr(self.shmm.lmuScorVeh(index).mDriverName)

    def vehicle_name(self, index: int | None = None) -> str:
        """Vehicle name"""
        return tostr(self.shmm.lmuScorVeh(index).mVehicleName)

    def class_name(self, index: int | None = None) -> str:
        """Vehicle class name"""
        return tostr(self.shmm.lmuScorVeh(index).mVehicleClass)

    def same_class(self, index: int | None = None) -> bool:
        """Is same vehicle class"""
        return self.shmm.lmuScorVeh(index).mVehicleClass == self.shmm.lmuScorVeh().mVehicleClass

    def total_vehicles(self) -> int:
        """Total vehicles"""
        return self.shmm.lmuScorInfo.mNumVehicles

    def place(self, index: int | None = None) -> int:
        """Vehicle overall place"""
        return self.shmm.lmuScorVeh(index).mPlace

    def qualification(self, index: int | None = None) -> int:
        """Vehicle qualification place"""
        return self.shmm.lmuScorVeh(index).mQualification

    def in_pits(self, index: int | None = None) -> bool:
        """Is in pits"""
        return self.shmm.lmuScorVeh(index).mInPits

    def in_garage(self, index: int | None = None) -> bool:
        """Is in garage"""
        return self.shmm.lmuScorVeh(index).mInGarageStall

    def in_paddock(self, index: int | None = None) -> int:
        """Is in paddock (either pit lane or garage), 0 = on track, 1 = pit lane, 2 = garage"""
        state = self.shmm.lmuScorVeh(index)
        return 2 if state.mInGarageStall else state.mInPits

    def number_pitstops(self, index: int | None = None, penalty: int = 0) -> int:
        """Number of pit stops"""
        return -penalty if penalty else self.shmm.lmuScorVeh(index).mNumPitstops

    def number_penalties(self, index: int | None = None) -> int:
        """Number of penalties"""
        return self.shmm.lmuScorVeh(index).mNumPenalties

    def pit_request(self, index: int | None = None) -> bool:
        """Is requested pit, 0 = none, 1 = request, 2 = entering, 3 = stopped, 4 = exiting"""
        return self.shmm.lmuScorVeh(index).mPitState == 1

    def pit_stop_time(self) -> float:
        """Estimated pit stop time (seconds)"""
        return self.rest.pitStopTime

    def absolute_refill(self) -> float:
        """Absolute refill fuel (liter) or virtual energy (percent)"""
        return self.rest.absoluteRefill

    def stint_usage(self, driver_name: str) -> tuple[float, float, float, float, int]:
        """Stint usage data"""
        return self.rest.stintUsage.get(driver_name, STINT_USAGE_DEFAULT)

    def finish_state(self, index: int | None = None) -> int:
        """Finish state, 0 = none, 1 = finished, 2 = DNF, 3 = DQ"""
        state = self.shmm.lmuScorVeh(index).mFinishStatus
        if state == 0:
            return 0
        if state == 1:
            return 1
        if state == 2:
            return 2
        if state == 3:
            return 3
        return 0

    def fuel(self, index: int | None = None) -> float:
        """Remaining fuel (liters)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mFuel)

    def tank_capacity(self, index: int | None = None) -> float:
        """Fuel tank capacity (liters)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mFuelCapacity)

    def virtual_energy(self, index: int | None = None) -> float:
        """Remaining virtual energy (fraction)"""
        return self.shmm.lmuTeleVeh(index).mVirtualEnergy

    def orientation_yaw_radians(self, index: int | None = None) -> float:
        """Orientation yaw (radians)"""
        ori = self.shmm.lmuTeleVeh(index).mOri[2]
        return rmnan(oriyaw2rad(ori.x, ori.z))

    def position_xyz(self, index: int | None = None) -> tuple[float, float, float]:
        """Raw x,y,z position (meters)"""
        pos = self.shmm.lmuTeleVeh(index).mPos
        return rmnan(pos.x), rmnan(pos.y), rmnan(pos.z)

    def position_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal axis position (meters) related to world plane"""
        return rmnan(self.shmm.lmuTeleVeh(index).mPos.x)  # in LMU coord system

    def position_lateral(self, index: int | None = None) -> float:
        """Lateral axis position (meters) related to world plane"""
        return -rmnan(self.shmm.lmuTeleVeh(index).mPos.z)  # in LMU coord system

    def position_vertical(self, index: int | None = None) -> float:
        """Vertical axis position (meters) related to world plane"""
        return rmnan(self.shmm.lmuTeleVeh(index).mPos.y)  # in LMU coord system

    def accel_lateral(self, index: int | None = None) -> float:
        """Lateral acceleration (m/s^2)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLocalAccel.x)  # X in LMU coord system

    def accel_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal acceleration (m/s^2)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLocalAccel.z)  # Z in LMU coord system

    def accel_vertical(self, index: int | None = None) -> float:
        """Vertical acceleration (m/s^2)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLocalAccel.y)  # Y in LMU coord system

    def velocity_lateral(self, index: int | None = None) -> float:
        """Lateral velocity (m/s) x"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLocalVel.x)  # X in LMU coord system

    def velocity_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal velocity (m/s) y"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLocalVel.z)  # Z in LMU coord system

    def velocity_vertical(self, index: int | None = None) -> float:
        """Vertical velocity (m/s) z"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLocalVel.y)  # Y in LMU coord system

    def speed(self, index: int | None = None) -> float:
        """Speed (m/s)"""
        vel = self.shmm.lmuTeleVeh(index).mLocalVel
        return rmnan(vel2speed(vel.x, vel.y, vel.z))

    def downforce_front(self, index: int | None = None) -> float:
        """Downforce front (Newtons)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mFrontDownforce)

    def downforce_rear(self, index: int | None = None) -> float:
        """Downforce rear (Newtons)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mRearDownforce)

    def damage_severity(self, index: int | None = None) -> tuple[int, int, int, int, int, int, int, int]:
        """Damage severity, sort row by row from left to right, top to bottom"""
        data = self.shmm.lmuTeleVeh(index)
        dmg = data.mDentSeverity
        dmg_rear = 3 if data.mDetached else dmg[4]  # the only body parts can detach in LMU is rear wing
        return dmg[1], dmg[0], dmg[7], dmg[2], dmg[6], dmg[3], dmg_rear, dmg[5]  # LMU order

    def aero_damage(self, index: int | None = None) -> float:
        """Aerodynamic damage (fraction), 0.0 no damage, 1.0 totaled"""
        return self.rest.aeroDamage

    def integrity(self, index: int | None = None) -> float:
        """Vehicle integrity"""
        data = self.shmm.lmuTeleVeh(index)
        total = (
            1
            - sum(data.mDentSeverity) / 16
            - any(wheel_data.mDetached for wheel_data in data.mWheels) / 2
            - data.mDetached / 2
        )
        if total < 0:
            return 0
        return total

    def is_detached(self, index: int | None = None) -> bool:
        """Whether any vehicle parts are detached"""
        return self.shmm.lmuTeleVeh(index).mDetached

    def impact_time(self, index: int | None = None) -> float:
        """Last impact time stamp (seconds)"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLastImpactET)

    def impact_magnitude(self, index: int | None = None) -> float:
        """Last impact magnitude"""
        return rmnan(self.shmm.lmuTeleVeh(index).mLastImpactMagnitude)

    def impact_position(self, index: int | None = None) -> tuple[float, float]:
        """Last impact position x,y coordinates"""
        pos = self.shmm.lmuTeleVeh(index).mLastImpactPos
        return -rmnan(pos.x), rmnan(pos.z)

    def setup(self) -> tuple[str, ...]:
        """Car setup data"""
        return self.rest.lastCarSetup


class Wheel(_reader.Wheel, DataAdapter):
    """Wheel & suspension (front left, front right, rear left, rear right)"""

    __slots__ = ()

    def camber(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel camber (radians)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mCamber),
            rmnan(wheel_data[1].mCamber),
            rmnan(wheel_data[2].mCamber),
            rmnan(wheel_data[3].mCamber),
        )

    def toe(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel toe (radians)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mToe),
            rmnan(wheel_data[1].mToe),
            rmnan(wheel_data[2].mToe),
            rmnan(wheel_data[3].mToe),
        )

    def toe_symmetric(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel toe symmetric (radians)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mToe),
            -rmnan(wheel_data[1].mToe),
            rmnan(wheel_data[2].mToe),
            -rmnan(wheel_data[3].mToe),
        )

    def rotation(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel rotation (radians per second)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mRotation),
            rmnan(wheel_data[1].mRotation),
            rmnan(wheel_data[2].mRotation),
            rmnan(wheel_data[3].mRotation),
        )

    def velocity_lateral(self, index: int | None = None) -> tuple[float, ...]:
        """Lateral velocity (m/s) x"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mLateralGroundVel),
            rmnan(wheel_data[1].mLateralGroundVel),
            rmnan(wheel_data[2].mLateralGroundVel),
            rmnan(wheel_data[3].mLateralGroundVel),
        )

    def velocity_longitudinal(self, index: int | None = None) -> tuple[float, ...]:
        """Longitudinal velocity (m/s) y"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mLongitudinalGroundVel),
            rmnan(wheel_data[1].mLongitudinalGroundVel),
            rmnan(wheel_data[2].mLongitudinalGroundVel),
            rmnan(wheel_data[3].mLongitudinalGroundVel),
        )

    def slip_angle_fl(self, index: int | None = None) -> float:
        """Slip angle (radians) front left"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels[0]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def slip_angle_fr(self, index: int | None = None) -> float:
        """Slip angle (radians) front right"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels[1]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def slip_angle_rl(self, index: int | None = None) -> float:
        """Slip angle (radians) rear left"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels[2]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def slip_angle_rr(self, index: int | None = None) -> float:
        """Slip angle (radians) rear right"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels[3]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def ride_height(self, index: int | None = None) -> tuple[float, ...]:
        """Ride height (convert meters to millimeters)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mRideHeight) * 1000,
            rmnan(wheel_data[1].mRideHeight) * 1000,
            rmnan(wheel_data[2].mRideHeight) * 1000,
            rmnan(wheel_data[3].mRideHeight) * 1000,
        )

    def third_spring_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Third spring deflection front & rear (convert meters to millimeters)"""
        wheel_data = self.shmm.lmuTeleVeh(index)
        front = rmnan(wheel_data.mFront3rdDeflection) * 1000
        rear = rmnan(wheel_data.mRear3rdDeflection) * 1000
        return (front, front, rear, rear)

    def suspension_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension deflection (convert meters to millimeters)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mSuspensionDeflection) * 1000,
            rmnan(wheel_data[1].mSuspensionDeflection) * 1000,
            rmnan(wheel_data[2].mSuspensionDeflection) * 1000,
            rmnan(wheel_data[3].mSuspensionDeflection) * 1000,
        )

    def suspension_force(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension force (Newtons)"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mSuspForce),
            rmnan(wheel_data[1].mSuspForce),
            rmnan(wheel_data[2].mSuspForce),
            rmnan(wheel_data[3].mSuspForce),
        )

    def suspension_damage(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension damage (fraction), 0.0 no damage, 1.0 totaled"""
        return self.rest.suspensionDamage

    def position_vertical(self, index: int | None = None) -> tuple[float, ...]:
        """Vertical wheel position (convert meters to millimeters) related to vehicle"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mWheelYLocation) * 1000,
            rmnan(wheel_data[1].mWheelYLocation) * 1000,
            rmnan(wheel_data[2].mWheelYLocation) * 1000,
            rmnan(wheel_data[3].mWheelYLocation) * 1000,
        )

    def is_detached(self, index: int | None = None) -> tuple[bool, ...]:
        """Whether wheel is detached"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return (
            wheel_data[0].mDetached,
            wheel_data[1].mDetached,
            wheel_data[2].mDetached,
            wheel_data[3].mDetached,
        )

    def offroad(self, index: int | None = None) -> int:
        """Number of wheels currently off the road"""
        wheel_data = self.shmm.lmuTeleVeh(index).mWheels
        return sum(2 <= data.mSurfaceType <= 4 for data in wheel_data)
