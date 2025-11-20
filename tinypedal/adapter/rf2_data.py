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
rF2 API data set

Notes:
    Convert all temperature (kelvin) to Celsius before output.
"""

from __future__ import annotations

from ..calculation import (
    clock_time_scale_sync,
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
from . import restapi_connector, rf2_connector


class DataAdapter:
    """Read & sort data into groups"""

    __slots__ = (
        "shmm",
        "rest",
    )

    def __init__(self, shmm: rf2_connector.RF2Info, rest: restapi_connector.RestAPIInfo) -> None:
        """Initialize API setting

        Args:
            shmm: shared memory API connector.
            rest: rest API connector.
        """
        self.shmm = shmm
        self.rest = rest


class State(DataAdapter):
    """State"""

    __slots__ = ()

    def active(self) -> bool:
        """Is active (driving or overriding)"""
        return self.shmm.isActive

    def paused(self) -> bool:
        """Is paused"""
        return self.shmm.isPaused

    def version(self) -> str:
        """Identify API version"""
        version = tostr(self.shmm.rf2Ext.mVersion)
        return version if version else "unknown"

    def identifier(self) -> str:
        """Identify API"""
        return self.shmm.identifier


class Brake(DataAdapter):
    """Brake"""

    __slots__ = ()

    def bias_front(self, index: int | None = None) -> float:
        """Brake bias front (fraction)"""
        return 1 - rmnan(self.shmm.rf2TeleVeh(index).mRearBrakeBias)

    def pressure(self, index: int | None = None, scale: float = 1) -> tuple[float, ...]:
        """Brake pressure (fraction)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mBrakePressure) * scale,
            rmnan(wheel_data[1].mBrakePressure) * scale,
            rmnan(wheel_data[2].mBrakePressure) * scale,
            rmnan(wheel_data[3].mBrakePressure) * scale,
        )

    def temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Brake temperature (Celsius)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mBrakeTemp) - 273.15,
            rmnan(wheel_data[1].mBrakeTemp) - 273.15,
            rmnan(wheel_data[2].mBrakeTemp) - 273.15,
            rmnan(wheel_data[3].mBrakeTemp) - 273.15,
        )

    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Brake remaining thickness (meters)"""
        return self.rest.telemetry.brakeWear


class ElectricMotor(DataAdapter):
    """Electric motor"""

    __slots__ = ()

    def state(self, index: int | None = None) -> int:
        """Motor state, 0 = n/a, 1 = off, 2 = drain, 3 = regen"""
        state = self.shmm.rf2TeleVeh(index).mElectricBoostMotorState
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
        return rmnan(self.shmm.rf2TeleVeh(index).mBatteryChargeFraction)

    def rpm(self, index: int | None = None) -> float:
        """Motor RPM (rev per minute)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mElectricBoostMotorRPM)

    def torque(self, index: int | None = None) -> float:
        """Motor torque (Nm)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mElectricBoostMotorTorque)

    def motor_temperature(self, index: int | None = None) -> float:
        """Motor temperature (Celsius)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mElectricBoostMotorTemperature)

    def water_temperature(self, index: int | None = None) -> float:
        """Motor water temperature (Celsius)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mElectricBoostWaterTemperature)


class Engine(DataAdapter):
    """Engine"""

    __slots__ = ()

    def gear(self, index: int | None = None) -> int:
        """Gear"""
        return self.shmm.rf2TeleVeh(index).mGear

    def gear_max(self, index: int | None = None) -> int:
        """Max gear"""
        return self.shmm.rf2TeleVeh(index).mMaxGears

    def rpm(self, index: int | None = None) -> float:
        """RPM (rev per minute)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mEngineRPM)

    def rpm_max(self, index: int | None = None) -> float:
        """Max RPM (rev per minute)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mEngineMaxRPM)

    def torque(self, index: int | None = None) -> float:
        """Torque (Nm)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mEngineTorque)

    def turbo(self, index: int | None = None) -> float:
        """Turbo pressure (Pa)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mTurboBoostPressure)

    def oil_temperature(self, index: int | None = None) -> float:
        """Oil temperature (Celsius)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mEngineOilTemp)

    def water_temperature(self, index: int | None = None) -> float:
        """Water temperature (Celsius)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mEngineWaterTemp)


class Inputs(DataAdapter):
    """Inputs"""

    __slots__ = ()

    def throttle(self, index: int | None = None) -> float:
        """Throttle filtered (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mFilteredThrottle)

    def throttle_raw(self, index: int | None = None) -> float:
        """Throttle raw (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mUnfilteredThrottle)

    def brake(self, index: int | None = None) -> float:
        """Brake filtered (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mFilteredBrake)

    def brake_raw(self, index: int | None = None) -> float:
        """Brake raw (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mUnfilteredBrake)

    def clutch(self, index: int | None = None) -> float:
        """Clutch filtered (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mFilteredClutch)

    def clutch_raw(self, index: int | None = None) -> float:
        """Clutch raw (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mUnfilteredClutch)

    def steering(self, index: int | None = None) -> float:
        """Steering filtered (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mFilteredSteering)

    def steering_raw(self, index: int | None = None) -> float:
        """Steering raw (fraction)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mUnfilteredSteering)

    def steering_shaft_torque(self, index: int | None = None) -> float:
        """Steering shaft torque (Nm)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mSteeringShaftTorque)

    def steering_range_physical(self, index: int | None = None) -> float:
        """Steering physical rotation range (degrees)"""
        rot_range = rmnan(self.shmm.rf2TeleVeh(index).mPhysicalSteeringWheelRange)
        if rot_range <= 0:
            rot_range = self.rest.telemetry.steeringWheelRange
        return rot_range

    def steering_range_visual(self, index: int | None = None) -> float:
        """Steering visual rotation range (degrees)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mVisualSteeringWheelRange)

    def force_feedback(self) -> float:
        """Steering force feedback (fraction)"""
        return rmnan(self.shmm.rf2Ffb.mForceValue)


class Lap(DataAdapter):
    """Lap"""

    __slots__ = ()

    def number(self, index: int | None = None) -> int:
        """Current lap number"""
        return self.shmm.rf2TeleVeh(index).mLapNumber

    def completed_laps(self, index: int | None = None) -> int:
        """Total completed laps"""
        return self.shmm.rf2ScorVeh(index).mTotalLaps

    def track_length(self) -> float:
        """Full lap or track length (meters)"""
        return rmnan(self.shmm.rf2ScorInfo.mLapDist)

    def distance(self, index: int | None = None) -> float:
        """Distance into lap (meters)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mLapDist)

    def progress(self, index: int | None = None) -> float:
        """Lap progress (fraction), distance into lap"""
        return rmnan(lap_progress_distance(
            self.shmm.rf2ScorVeh(index).mLapDist,
            self.shmm.rf2ScorInfo.mLapDist))

    def maximum(self) -> int:
        """Maximum lap"""
        return self.shmm.rf2ScorInfo.mMaxLaps

    def sector_index(self, index: int | None = None) -> int:
        """Sector index, 0 = S1, 1 = S2, 2 = S3"""
        # RF2 sector index 0 = S3, index 1 = S1, index 2 = S2
        sector = self.shmm.rf2ScorVeh(index).mSector
        if sector == 0:
            return 2
        if sector == 1:
            return 0
        return 1

    def behind_leader(self, index: int | None = None) -> int:
        """Laps behind leader"""
        return self.shmm.rf2ScorVeh(index).mLapsBehindLeader

    def behind_next(self, index: int | None = None) -> int:
        """Laps behind next place"""
        return self.shmm.rf2ScorVeh(index).mLapsBehindNext


class Session(DataAdapter):
    """Session"""

    __slots__ = ()

    def combo_name(self) -> str:
        """Track & vehicle combo name, strip off invalid char"""
        track_name = tostr(self.shmm.rf2ScorInfo.mTrackName)
        class_name = tostr(self.shmm.rf2ScorVeh().mVehicleClass)
        return strip_invalid_char(f"{track_name} - {class_name}")

    def track_name(self) -> str:
        """Track name, strip off invalid char"""
        return strip_invalid_char(tostr(self.shmm.rf2ScorInfo.mTrackName))

    def identifier(self) -> tuple[int, int, int]:
        """Identify session"""
        session_length = rmnan(self.shmm.rf2ScorInfo.mEndET)
        session_type = self.shmm.rf2ScorInfo.mSession
        session_stamp = int(session_length * 100 + session_type)
        session_etime = int(rmnan(self.shmm.rf2ScorInfo.mCurrentET))
        session_tlaps = self.shmm.rf2ScorVeh().mTotalLaps
        return session_stamp, session_etime, session_tlaps

    def elapsed(self) -> float:
        """Session elapsed time (seconds)"""
        return rmnan(self.shmm.rf2ScorInfo.mCurrentET)

    def start(self) -> float:
        """Session start time (seconds)"""
        return rmnan(self.shmm.rf2ScorInfo.mStartET)

    def end(self) -> float:
        """Session end time (seconds)"""
        return rmnan(self.shmm.rf2ScorInfo.mEndET)

    def remaining(self) -> float:
        """Session time remaining (seconds)"""
        scor = self.shmm.rf2ScorInfo
        return rmnan(scor.mEndET - scor.mCurrentET)

    def session_type(self) -> int:
        """Session type, 0 = TESTDAY, 1 = PRACTICE, 2 = QUALIFY, 3 = WARMUP, 4 = RACE"""
        session = self.shmm.rf2ScorInfo.mSession
        if session >= 10:  # race
            return 4
        if session == 9:  # warmup
            return 3
        if session >= 5:  # qualify
            return 2
        if session >= 1:  # practice
            return 1
        return 0  # test day

    def lap_type(self) -> bool:
        """Is lap type session, false for time type"""
        return self.shmm.rf2ScorInfo.mMaxLaps < 99999

    def in_race(self) -> bool:
        """Is in race session"""
        return self.shmm.rf2ScorInfo.mSession > 9

    def private_qualifying(self) -> bool:
        """Is private qualifying"""
        return self.rest.telemetry.privateQualifying == 1

    def in_countdown(self) -> bool:
        """Is in countdown phase before race"""
        return self.shmm.rf2ScorInfo.mGamePhase == 4

    def in_formation(self) -> bool:
        """Is in formation phase before race"""
        return self.shmm.rf2ScorInfo.mGamePhase == 3

    def pit_open(self) -> bool:
        """Is pit lane open"""
        return self.shmm.rf2ScorInfo.mGamePhase > 0

    def pre_race(self) -> bool:
        """Before race starts (green flag)"""
        return self.shmm.rf2ScorInfo.mGamePhase <= 4

    def green_flag(self) -> bool:
        """Green flag (race starts)"""
        # Inaccurate due to 5FPS refresh rate from API
        return self.shmm.rf2ScorInfo.mGamePhase == 5

    def blue_flag(self, index: int | None = None) -> bool:
        """Is under blue flag"""
        return self.shmm.rf2ScorVeh(index).mFlag == 6

    def yellow_flag(self) -> bool:
        """Is there yellow flag in any sectors"""
        sec_flag = self.shmm.rf2ScorInfo.mSectorFlag
        return any(data == 1 for data in sec_flag)

    def start_lights(self) -> int:
        """Start lights countdown sequence"""
        scor = self.shmm.rf2ScorInfo
        return scor.mNumRedLights - scor.mStartLight + 1

    def track_temperature(self) -> float:
        """Track temperature (Celsius)"""
        return rmnan(self.shmm.rf2ScorInfo.mTrackTemp)

    def ambient_temperature(self) -> float:
        """Ambient temperature (Celsius)"""
        return rmnan(self.shmm.rf2ScorInfo.mAmbientTemp)

    def raininess(self) -> float:
        """Rain severity (fraction)"""
        return rmnan(self.shmm.rf2ScorInfo.mRaining)

    def wetness_minimum(self) -> float:
        """Road minimum wetness (fraction)"""
        return rmnan(self.shmm.rf2ScorInfo.mMinPathWetness)

    def wetness_maximum(self) -> float:
        """Road maximum wetness (fraction)"""
        return rmnan(self.shmm.rf2ScorInfo.mMaxPathWetness)

    def wetness_average(self) -> float:
        """Road average wetness (fraction)"""
        return rmnan(self.shmm.rf2ScorInfo.mAvgPathWetness)

    def wetness(self) -> tuple[float, float, float]:
        """Road wetness set (fraction)"""
        scor = self.shmm.rf2ScorInfo
        return (rmnan(scor.mMinPathWetness),
                rmnan(scor.mMaxPathWetness),
                rmnan(scor.mAvgPathWetness))

    def weather_forecast(self) -> tuple[WeatherNode, ...]:
        """Weather forecast nodes"""
        session_type = self.shmm.rf2ScorInfo.mSession
        if session_type <= 1:  # practice session
            return self.rest.telemetry.forecastPractice
        if session_type == 2:  # qualify session
            return self.rest.telemetry.forecastQualify
        return self.rest.telemetry.forecastRace  # race session

    def time_scale(self) -> int:
        """Time scale"""
        track_time = self.rest.telemetry.trackClockTime
        if track_time == -1:  # trackClockTime unavailable
            time_scale = max(self.rest.telemetry.timeScale, 0)
        else:  # sync time scale
            time_scale = clock_time_scale_sync(track_time, self.elapsed(), self.start())
        return time_scale


class Switch(DataAdapter):
    """Switch"""

    __slots__ = ()

    def headlights(self, index: int | None = None) -> int:
        """Headlights"""
        return self.shmm.rf2TeleVeh(index).mHeadlights

    def ignition_starter(self, index: int | None = None) -> int:
        """Ignition"""
        return self.shmm.rf2TeleVeh(index).mIgnitionStarter

    def speed_limiter(self, index: int | None = None) -> int:
        """Speed limiter"""
        return self.shmm.rf2TeleVeh(index).mSpeedLimiter

    def drs_status(self, index: int | None = None) -> int:
        """DRS status, 0 not_available, 1 available, 2 allowed(not activated), 3 activated"""
        tele_veh = self.shmm.rf2TeleVeh(index)
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
        return bool(self.shmm.rf2Ext.mPhysics.mAutoClutch)


class Timing(DataAdapter):
    """Timing"""

    __slots__ = ()

    def start(self, index: int | None = None) -> float:
        """Current lap start time (seconds)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLapStartET)

    def elapsed(self, index: int | None = None) -> float:
        """Current lap elapsed time (seconds)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mElapsedTime)

    def current_laptime(self, index: int | None = None) -> float:
        """Current lap time (seconds)"""
        tele_veh = self.shmm.rf2TeleVeh(index)
        return rmnan(tele_veh.mElapsedTime - tele_veh.mLapStartET)

    def last_laptime(self, index: int | None = None) -> float:
        """Last lap time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mLastLapTime)

    def best_laptime(self, index: int | None = None) -> float:
        """Best lap time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mBestLapTime)

    def reference_laptime(self, index: int | None = None):
        """Reference lap time (seconds)"""
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
        return rmnan(self.shmm.rf2ScorVeh(index).mEstimatedLapTime)

    def estimated_time_into(self, index: int | None = None) -> float:
        """Estimated time into lap (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mTimeIntoLap)

    def current_sector1(self, index: int | None = None) -> float:
        """Current lap sector 1 time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mCurSector1)

    def current_sector2(self, index: int | None = None) -> float:
        """Current lap sector 1+2 time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mCurSector2)

    def last_sector1(self, index: int | None = None) -> float:
        """Last lap sector 1 time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mLastSector1)

    def last_sector2(self, index: int | None = None) -> float:
        """Last lap sector 1+2 time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mLastSector2)

    def best_sector1(self, index: int | None = None) -> float:
        """Best lap sector 1 time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mBestSector1)

    def best_sector2(self, index: int | None = None) -> float:
        """Best lap sector 1+2 time (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mBestSector2)

    def behind_leader(self, index: int | None = None) -> float:
        """Time behind leader (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mTimeBehindLeader)

    def behind_next(self, index: int | None = None) -> float:
        """Time behind next place (seconds)"""
        return rmnan(self.shmm.rf2ScorVeh(index).mTimeBehindNext)


class Tyre(DataAdapter):
    """Tyre"""

    __slots__ = ()

    def compound_front(self, index: int | None = None) -> int:
        """Tyre compound (front)"""
        return self.shmm.rf2TeleVeh(index).mFrontTireCompoundIndex

    def compound_rear(self, index: int | None = None) -> int:
        """Tyre compound (rear)"""
        return self.shmm.rf2TeleVeh(index).mRearTireCompoundIndex

    def compound(self, index: int | None = None) -> tuple[int, int]:
        """Tyre compound set (front, rear)"""
        tele_veh = self.shmm.rf2TeleVeh(index)
        return tele_veh.mFrontTireCompoundIndex, tele_veh.mRearTireCompoundIndex

    def compound_name_front(self, index: int | None = None) -> str:
        """Tyre compound name (front)"""
        return tostr(self.shmm.rf2TeleVeh(index).mFrontTireCompoundName)

    def compound_name_rear(self, index: int | None = None) -> str:
        """Tyre compound name (rear)"""
        return tostr(self.shmm.rf2TeleVeh(index).mRearTireCompoundName)

    def compound_name(self, index: int | None = None) -> tuple[str, str]:
        """Tyre compound name set (front, rear)"""
        tele_veh = self.shmm.rf2TeleVeh(index)
        return tostr(tele_veh.mFrontTireCompoundName), tostr(tele_veh.mRearTireCompoundName)

    def surface_temperature_avg(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) average"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(mean(wheel_data[0].mTemperature)) - 273.15,
            rmnan(mean(wheel_data[1].mTemperature)) - 273.15,
            rmnan(mean(wheel_data[2].mTemperature)) - 273.15,
            rmnan(mean(wheel_data[3].mTemperature)) - 273.15,
        )

    def surface_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) inner,center,outer"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
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
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(mean(wheel_data[0].mTireInnerLayerTemperature)) - 273.15,
            rmnan(mean(wheel_data[1].mTireInnerLayerTemperature)) - 273.15,
            rmnan(mean(wheel_data[2].mTireInnerLayerTemperature)) - 273.15,
            rmnan(mean(wheel_data[3].mTireInnerLayerTemperature)) - 273.15,
        )

    def inner_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre inner temperature set (Celsius) inner,center,outer"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
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
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mPressure),
            rmnan(wheel_data[1].mPressure),
            rmnan(wheel_data[2].mPressure),
            rmnan(wheel_data[3].mPressure),
        )

    def load(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre load (Newtons)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mTireLoad),
            rmnan(wheel_data[1].mTireLoad),
            rmnan(wheel_data[2].mTireLoad),
            rmnan(wheel_data[3].mTireLoad),
        )

    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre wear (fraction)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mWear),
            rmnan(wheel_data[1].mWear),
            rmnan(wheel_data[2].mWear),
            rmnan(wheel_data[3].mWear),
        )

    def carcass_temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre carcass temperature (Celsius)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mTireCarcassTemperature) - 273.15,
            rmnan(wheel_data[1].mTireCarcassTemperature) - 273.15,
            rmnan(wheel_data[2].mTireCarcassTemperature) - 273.15,
            rmnan(wheel_data[3].mTireCarcassTemperature) - 273.15,
        )


class Vehicle(DataAdapter):
    """Vehicle"""

    __slots__ = ()

    def is_player(self, index: int=0) -> bool:
        """Is local player"""
        return self.shmm.isPlayer(index)

    def is_driving(self) -> bool:
        """Is local player driving or in monitor"""
        return self.shmm.rf2TeleVeh().mIgnitionStarter > 0

    def player_index(self) -> int:
        """Get Local player index"""
        return self.shmm.playerIndex

    def slot_id(self, index: int | None = None) -> int:
        """Vehicle slot id"""
        return self.shmm.rf2ScorVeh(index).mID

    def driver_name(self, index: int | None = None) -> str:
        """Driver name"""
        return tostr(self.shmm.rf2ScorVeh(index).mDriverName)

    def vehicle_name(self, index: int | None = None) -> str:
        """Vehicle name"""
        return tostr(self.shmm.rf2ScorVeh(index).mVehicleName)

    def class_name(self, index: int | None = None) -> str:
        """Vehicle class name"""
        return tostr(self.shmm.rf2ScorVeh(index).mVehicleClass)

    def same_class(self, index: int | None = None) -> bool:
        """Is same vehicle class"""
        return self.shmm.rf2ScorVeh(index).mVehicleClass == self.shmm.rf2ScorVeh().mVehicleClass

    def total_vehicles(self) -> int:
        """Total vehicles"""
        return self.shmm.rf2ScorInfo.mNumVehicles

    def place(self, index: int | None = None) -> int:
        """Vehicle overall place"""
        return self.shmm.rf2ScorVeh(index).mPlace

    def qualification(self, index: int | None = None) -> int:
        """Vehicle qualification place"""
        return self.shmm.rf2ScorVeh(index).mQualification

    def in_pits(self, index: int | None = None) -> bool:
        """Is in pits"""
        return self.shmm.rf2ScorVeh(index).mInPits

    def in_garage(self, index: int | None = None) -> bool:
        """Is in garage"""
        return self.shmm.rf2ScorVeh(index).mInGarageStall

    def in_paddock(self, index: int | None = None) -> int:
        """Is in paddock (either pit lane or garage), 0 = on track, 1 = pit lane, 2 = garage"""
        state = self.shmm.rf2ScorVeh(index)
        return 2 if state.mInGarageStall else state.mInPits

    def number_pitstops(self, index: int | None = None, penalty: int = 0) -> int:
        """Number of pit stops"""
        return -penalty if penalty else self.shmm.rf2ScorVeh(index).mNumPitstops

    def number_penalties(self, index: int | None = None) -> int:
        """Number of penalties"""
        return self.shmm.rf2ScorVeh(index).mNumPenalties

    def penalty_duration(self, index: int | None = None) -> float:
        """Penalty duration (seconds)"""
        return self.rest.telemetry.penaltyTime

    def pit_request(self, index: int | None = None) -> bool:
        """Is requested pit, 0 = none, 1 = request, 2 = entering, 3 = stopped, 4 = exiting"""
        return self.shmm.rf2ScorVeh(index).mPitState == 1

    def pit_estimate(self, index: int | None = None) -> tuple[float, float, float, float, int]:
        """Pit stop estimate data, 0 min_pitstop_time, 1 max_pitstop_time, 2 refill_fuel, 3 refill_energy, 4 state_stopgo"""
        return self.rest.telemetry.pitStopEstimate

    def stint_usage(self, driver_name: str) -> tuple[float, float, float, float, int]:
        """Stint usage data"""
        return self.rest.telemetry.stintUsage.get(driver_name, STINT_USAGE_DEFAULT)

    def finish_state(self, index: int | None = None) -> int:
        """Finish state, 0 = none, 1 = finished, 2 = DNF, 3 = DQ"""
        state = self.shmm.rf2ScorVeh(index).mFinishStatus
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
        return rmnan(self.shmm.rf2TeleVeh(index).mFuel)

    def tank_capacity(self, index: int | None = None) -> float:
        """Fuel tank capacity (liters)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mFuelCapacity)

    def virtual_energy(self, index: int | None = None) -> float:
        """Remaining virtual energy (joule)"""
        return self.rest.telemetry.currentVirtualEnergy

    def max_virtual_energy(self, index: int | None = None) -> float:
        """Max virtual energy (joule)"""
        return self.rest.telemetry.maxVirtualEnergy

    def orientation_yaw_radians(self, index: int | None = None) -> float:
        """Orientation yaw (radians)"""
        ori = self.shmm.rf2TeleVeh(index).mOri[2]
        return rmnan(oriyaw2rad(ori.x, ori.z))

    def position_xyz(self, index: int | None = None) -> tuple[float, float, float]:
        """Raw x,y,z position (meters)"""
        pos = self.shmm.rf2TeleVeh(index).mPos
        return rmnan(pos.x), rmnan(pos.y), rmnan(pos.z)

    def position_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal axis position (meters) related to world plane"""
        return rmnan(self.shmm.rf2TeleVeh(index).mPos.x)  # in RF2 coord system

    def position_lateral(self, index: int | None = None) -> float:
        """Lateral axis position (meters) related to world plane"""
        return -rmnan(self.shmm.rf2TeleVeh(index).mPos.z)  # in RF2 coord system

    def position_vertical(self, index: int | None = None) -> float:
        """Vertical axis position (meters) related to world plane"""
        return rmnan(self.shmm.rf2TeleVeh(index).mPos.y)  # in RF2 coord system

    def accel_lateral(self, index: int | None = None) -> float:
        """Lateral acceleration (m/s^2)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLocalAccel.x)  # X in RF2 coord system

    def accel_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal acceleration (m/s^2)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLocalAccel.z)  # Z in RF2 coord system

    def accel_vertical(self, index: int | None = None) -> float:
        """Vertical acceleration (m/s^2)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLocalAccel.y)  # Y in RF2 coord system

    def velocity_lateral(self, index: int | None = None) -> float:
        """Lateral velocity (m/s) x"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLocalVel.x)  # X in RF2 coord system

    def velocity_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal velocity (m/s) y"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLocalVel.z)  # Z in RF2 coord system

    def velocity_vertical(self, index: int | None = None) -> float:
        """Vertical velocity (m/s) z"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLocalVel.y)  # Y in RF2 coord system

    def speed(self, index: int | None = None) -> float:
        """Speed (m/s)"""
        vel = self.shmm.rf2TeleVeh(index).mLocalVel
        return rmnan(vel2speed(vel.x, vel.y, vel.z))

    def downforce_front(self, index: int | None = None) -> float:
        """Downforce front (Newtons)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mFrontDownforce)

    def downforce_rear(self, index: int | None = None) -> float:
        """Downforce rear (Newtons)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mRearDownforce)

    def damage_severity(self, index: int | None = None) -> tuple[int, int, int, int, int, int, int, int]:
        """Damage severity, sort row by row from left to right, top to bottom"""
        dmg = self.shmm.rf2TeleVeh(index).mDentSeverity
        return dmg[1], dmg[0], dmg[7], dmg[2], dmg[6], dmg[3], dmg[4], dmg[5]  # RF2 order

    def aero_damage(self, index: int | None = None) -> float:
        """Aerodynamic damage (fraction), 0.0 no damage, 1.0 totaled"""
        return self.rest.telemetry.aeroDamage

    def integrity(self, index: int | None = None) -> float:
        """Vehicle integrity"""
        data = self.shmm.rf2TeleVeh(index)
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
        return self.shmm.rf2TeleVeh(index).mDetached

    def impact_time(self, index: int | None = None) -> float:
        """Last impact time stamp (seconds)"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLastImpactET)

    def impact_magnitude(self, index: int | None = None) -> float:
        """Last impact magnitude"""
        return rmnan(self.shmm.rf2TeleVeh(index).mLastImpactMagnitude)

    def impact_position(self, index: int | None = None) -> tuple[float, float]:
        """Last impact position x,y coordinates"""
        pos = self.shmm.rf2TeleVeh(index).mLastImpactPos
        return -rmnan(pos.x), rmnan(pos.z)


class Wheel(DataAdapter):
    """Wheel & suspension"""

    __slots__ = ()

    def camber(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel camber (radians)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mCamber),
            rmnan(wheel_data[1].mCamber),
            rmnan(wheel_data[2].mCamber),
            rmnan(wheel_data[3].mCamber),
        )

    def toe(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel toe (radians)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mToe),
            rmnan(wheel_data[1].mToe),
            rmnan(wheel_data[2].mToe),
            rmnan(wheel_data[3].mToe),
        )

    def toe_symmetric(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel toe symmetric (radians)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mToe),
            -rmnan(wheel_data[1].mToe),
            rmnan(wheel_data[2].mToe),
            -rmnan(wheel_data[3].mToe),
        )

    def rotation(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel rotation (radians per second)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mRotation),
            rmnan(wheel_data[1].mRotation),
            rmnan(wheel_data[2].mRotation),
            rmnan(wheel_data[3].mRotation),
        )

    def velocity_lateral(self, index: int | None = None) -> tuple[float, ...]:
        """Lateral velocity (m/s) x"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mLateralGroundVel),
            rmnan(wheel_data[1].mLateralGroundVel),
            rmnan(wheel_data[2].mLateralGroundVel),
            rmnan(wheel_data[3].mLateralGroundVel),
        )

    def velocity_longitudinal(self, index: int | None = None) -> tuple[float, ...]:
        """Longitudinal velocity (m/s) y"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mLongitudinalGroundVel),
            rmnan(wheel_data[1].mLongitudinalGroundVel),
            rmnan(wheel_data[2].mLongitudinalGroundVel),
            rmnan(wheel_data[3].mLongitudinalGroundVel),
        )

    def slip_angle_fl(self, index: int | None = None) -> float:
        """Slip angle (radians) front left"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels[0]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def slip_angle_fr(self, index: int | None = None) -> float:
        """Slip angle (radians) front right"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels[1]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def slip_angle_rl(self, index: int | None = None) -> float:
        """Slip angle (radians) rear left"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels[2]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def slip_angle_rr(self, index: int | None = None) -> float:
        """Slip angle (radians) rear right"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels[3]
        return rmnan(slip_angle(
            wheel_data.mLateralGroundVel,
            wheel_data.mLongitudinalGroundVel))

    def ride_height(self, index: int | None = None) -> tuple[float, ...]:
        """Ride height (convert meters to millmeters)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mRideHeight) * 1000,
            rmnan(wheel_data[1].mRideHeight) * 1000,
            rmnan(wheel_data[2].mRideHeight) * 1000,
            rmnan(wheel_data[3].mRideHeight) * 1000,
        )

    def third_spring_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Third spring deflection front & rear (convert meters to millmeters)"""
        wheel_data = self.shmm.rf2TeleVeh(index)
        front = rmnan(wheel_data.mFront3rdDeflection) * 1000
        rear = rmnan(wheel_data.mRear3rdDeflection) * 1000
        return (front, front, rear, rear)

    def suspension_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension deflection (convert meters to millmeters)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mSuspensionDeflection) * 1000,
            rmnan(wheel_data[1].mSuspensionDeflection) * 1000,
            rmnan(wheel_data[2].mSuspensionDeflection) * 1000,
            rmnan(wheel_data[3].mSuspensionDeflection) * 1000,
        )

    def suspension_force(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension force (Newtons)"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mSuspForce),
            rmnan(wheel_data[1].mSuspForce),
            rmnan(wheel_data[2].mSuspForce),
            rmnan(wheel_data[3].mSuspForce),
        )

    def suspension_damage(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension damage (fraction), 0.0 no damage, 1.0 totaled"""
        return self.rest.telemetry.suspensionDamage

    def position_vertical(self, index: int | None = None) -> tuple[float, ...]:
        """Vertical wheel position (convert meters to millmeters) related to vehicle"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            rmnan(wheel_data[0].mWheelYLocation) * 1000,
            rmnan(wheel_data[1].mWheelYLocation) * 1000,
            rmnan(wheel_data[2].mWheelYLocation) * 1000,
            rmnan(wheel_data[3].mWheelYLocation) * 1000,
        )

    def is_detached(self, index: int | None = None) -> tuple[bool, ...]:
        """Whether wheel is detached"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return (
            bool(wheel_data[0].mDetached),
            bool(wheel_data[1].mDetached),
            bool(wheel_data[2].mDetached),
            bool(wheel_data[3].mDetached),
        )

    def is_offroad(self, index: int | None = None) -> bool:
        """Whether all wheels are complete offroad"""
        wheel_data = self.shmm.rf2TeleVeh(index).mWheels
        return all(2 <= data.mSurfaceType <= 4 for data in wheel_data)
