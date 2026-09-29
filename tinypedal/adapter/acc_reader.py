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
ACC API data reader
"""

from __future__ import annotations

from math import atan2, pi

from ..calculation import mean, min_nonzero
from ..constant import DATA
from ..formatter import strip_invalid_char
from ..validator import bytes_to_str as tostr
from ..validator import infnan_to_zero as rmnan
from . import _reader
from .acc_sharedmemory import ACCInfo, acc_enum, acc_udp

ACC_CAR_MODEL = acc_enum.ACC_CAR_MODEL
ACC_CAR_MODEL_ID = acc_enum.ACC_CAR_MODEL_ID
ACC_TRACK_NAME = acc_enum.ACC_TRACK_NAME
ACC_TRACK_YEAR = acc_enum.ACC_TRACK_YEAR
ACC_TRACK_LENGTH = acc_enum.ACC_TRACK_LENGTH
ACC_CAR_CLASS = acc_enum.ACC_CAR_CLASS
ACC_BRAKEBIAS_OFFSET = acc_enum.ACC_BRAKEBIAS_OFFSET
ACC_MAX_STEERING_RANGE = acc_enum.ACC_MAX_STEERING_RANGE
ACC_TO_RF2_SKY_TYPE = acc_enum.dict_map({
    0: 1,
    1: 5,
    2: 7,
    3: 8,
    4: 9,
    5: 10,
}, default=0)


class DataAdapter:
    """Read & sort data into groups"""

    __slots__ = (
        "shmm",
        "udp",
    )

    def __init__(self, shmm: ACCInfo, udp: acc_udp.UDPBroadcastOutput) -> None:
        """Initialize API setting

        Args:
            shmm: shared memory API data.
            udp: UDP API data.
        """
        self.shmm = shmm
        self.udp = udp

    def udp_carinfo(self, index: int) -> acc_udp.UDPCarInfo:
        """Get car info from UDP API"""
        car_id = self.shmm.accGraphicsInfo.carIDs[index]
        return self.udp.entryList.entryListCars[car_id]


class State(_reader.State, DataAdapter):
    """State"""

    __slots__ = ()

    def active(self) -> bool:
        """Is active (driving or overriding)"""
        return self.shmm.isActive

    def paused(self) -> bool:
        """Is paused"""
        return self.shmm.isPaused

    def resets(self) -> int:
        """Number of player vehicle resets"""
        return self.shmm.vehicleResets

    def version(self) -> str:
        """Identify API version"""
        version = self.shmm.accStaticInfo.smVersion
        return version if version else DATA.TEXT_NA


class Brake(_reader.Brake, DataAdapter):
    """Brake"""

    __slots__ = ()

    def compound_name(self, index: int | None = None) -> tuple[str, str]:
        """Brake compound name, front, rear"""
        front = f"Pad {self.shmm.accPhysicsInfo.frontBrakeCompound + 1}"
        rear = f"Pad {self.shmm.accPhysicsInfo.rearBrakeCompound + 1}"
        return front, rear

    def bias_front(self, index: int | None = None) -> float:
        """Brake bias front (fraction)"""
        return rmnan(self.shmm.accPhysicsInfo.brakeBias + ACC_BRAKEBIAS_OFFSET(self.shmm.accStaticInfo.carModel) * 0.01)

    def migration(self, index: int | None = None) -> float:
        """Brake migration (percent)"""
        return 0.0

    def pressure(self, index: int | None = None, scale: float = 1) -> tuple[float, ...]:
        """Brake pressure (fraction)"""
        data = self.shmm.accPhysicsInfo
        bias_front_raw = data.brakeBias
        bias_offset = ACC_BRAKEBIAS_OFFSET(self.shmm.accStaticInfo.carModel)
        if bias_offset:
            bias_front_adjusted = bias_front_raw + bias_offset * 0.01
            bias_rear_raw = 1 - bias_front_raw
            bias_rear_adjusted = 1 - bias_front_adjusted
            bias_front_scale = bias_front_adjusted / bias_front_raw if bias_front_raw > 0 else 1
            bias_rear_scale = bias_rear_adjusted / bias_rear_raw if bias_rear_raw > 0 else 1
        else:
            bias_front_scale = 1
            bias_rear_scale = 1
        return (
            rmnan(data.brakePressure[0]) * bias_front_scale * scale,
            rmnan(data.brakePressure[1]) * bias_front_scale * scale,
            rmnan(data.brakePressure[2]) * bias_rear_scale * scale,
            rmnan(data.brakePressure[3]) * bias_rear_scale * scale,
        )

    def temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Brake temperature (Celsius)"""
        data = self.shmm.accPhysicsInfo.brakeTemp
        return (
            rmnan(data[0]),
            rmnan(data[1]),
            rmnan(data[2]),
            rmnan(data[3]),
        )

    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Brake remaining thickness (meters)"""
        data = self.shmm.accPhysicsInfo.padLife
        return (
            rmnan(data[0]) * 0.001,
            rmnan(data[1]) * 0.001,
            rmnan(data[2]) * 0.001,
            rmnan(data[3]) * 0.001,
        )


class ElectricMotor(_reader.ElectricMotor, DataAdapter):
    """Electric motor"""

    __slots__ = ()

    def state(self, index: int | None = None) -> int:
        """Motor state, 0 = n/a, 1 = off, 2 = drain, 3 = regen"""
        return 0

    def battery_charge(self, index: int | None = None) -> float:
        """Battery charge (fraction)"""
        return 0.0

    def rpm(self, index: int | None = None) -> float:
        """Motor RPM (rev per minute)"""
        return 0.0

    def torque(self, index: int | None = None) -> float:
        """Motor torque (Nm)"""
        return 0.0

    def motor_temperature(self, index: int | None = None) -> float:
        """Motor temperature (Celsius)"""
        return 0.0

    def water_temperature(self, index: int | None = None) -> float:
        """Motor water temperature (Celsius)"""
        return 0.0

    def regeneration_level(self, index: int | None = None) -> float:
        """Regeneration level (kW)"""
        return 0.0


class Engine(_reader.Engine, DataAdapter):
    """Engine"""

    __slots__ = ()

    def gear(self, index: int | None = None) -> int:
        """Gear"""
        return self.shmm.accPhysicsInfo.gear - 1

    def gear_max(self, index: int | None = None) -> int:
        """Max gear"""
        return 6

    def rpm(self, index: int | None = None) -> float:
        """RPM (rev per minute)"""
        return self.shmm.accPhysicsInfo.rpm

    def rpm_max(self, index: int | None = None) -> float:
        """Max RPM (rev per minute)"""
        return self.shmm.accPhysicsInfo.currentMaxRPM

    def torque(self, index: int | None = None) -> float:
        """Torque (Nm)"""
        return 0.0

    def turbo(self, index: int | None = None) -> float:
        """Turbo pressure (Pa)"""
        return 0.0

    def oil_temperature(self, index: int | None = None) -> float:
        """Oil temperature (Celsius)"""
        return 0.0

    def water_temperature(self, index: int | None = None) -> float:
        """Water temperature (Celsius)"""
        return rmnan(self.shmm.accPhysicsInfo.waterTemp)

    def exhaust_temperature(self, index: int | None = None) -> float:
        """Exhaust temperature (Celsius)"""
        return rmnan(self.shmm.accGraphicsInfo.exhaustTemperature)

    def lift_and_coast_progress(self, index: int | None = None) -> float:
        """Lift and coast progress (fraction), range 0.0 to 1.0"""
        return 0.0

    def fuel(self, index: int | None = None) -> float:
        """Remaining fuel (liters)"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accPhysicsInfo.fuel)
        return 0.0

    def fuel_fraction(self, index: int | None = None) -> float:
        """Remaining fuel (fraction)"""
        return 0.0

    def tank_capacity(self, index: int | None = None) -> float:
        """Fuel tank capacity (liters)"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accStaticInfo.maxFuel)
        return 0.0

    def virtual_energy(self, index: int | None = None) -> float:
        """Remaining virtual energy (fraction)"""
        return 0.0

    def max_virtual_energy(self) -> float:
        """Maximum virtual energy (joule)"""
        return 0.0

    def absolute_refill(self) -> float:
        """Absolute refill fuel (liter) or virtual energy (percent)"""
        total = self.shmm.accGraphicsInfo.mfdFuelToAdd + self.shmm.accPhysicsInfo.fuel
        return rmnan(min(total, self.shmm.accStaticInfo.maxFuel))


class Inputs(_reader.Inputs, DataAdapter):
    """Inputs"""

    __slots__ = ()

    def throttle(self, index: int | None = None) -> float:
        """Throttle filtered (fraction)"""
        data = self.shmm.accPhysicsInfo
        return rmnan(data.throttle * (1 - data.tc))

    def throttle_raw(self, index: int | None = None) -> float:
        """Throttle raw (fraction)"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accPhysicsInfo.throttle)
        return 0.0

    def brake(self, index: int | None = None) -> float:
        """Brake filtered (fraction)"""
        data = self.shmm.accPhysicsInfo
        return rmnan(data.brake * (1 - data.abs))

    def brake_raw(self, index: int | None = None) -> float:
        """Brake raw (fraction)"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accPhysicsInfo.brake)
        return 0.0

    def clutch(self, index: int | None = None) -> float:
        """Clutch filtered (fraction)"""
        return rmnan(self.shmm.accPhysicsInfo.clutch)

    def clutch_raw(self, index: int | None = None) -> float:
        """Clutch raw (fraction)"""
        return rmnan(self.shmm.accPhysicsInfo.clutch)

    def steering(self, index: int | None = None) -> float:
        """Steering (fraction)"""
        return rmnan(self.shmm.accPhysicsInfo.steerAngle)

    def steering_range(self, index: int | None = None) -> float:
        """Steering physical rotation range (degrees)"""
        return ACC_MAX_STEERING_RANGE(self.shmm.accStaticInfo.carModel)

    def force_feedback(self) -> float:
        """Steering force feedback (fraction)"""
        return rmnan(self.shmm.accPhysicsInfo.forceFeedback)


class Lap(_reader.Lap, DataAdapter):
    """Lap"""

    __slots__ = ()

    def completed(self, index: int | None = None) -> int:
        """Total completed laps"""
        if index is None:  # or index == self.shmm.playerIndex:
            return self.shmm.accGraphicsInfo.completedLaps
        return self.udp_carinfo(index).completedLaps

    def track_length(self) -> float:
        """Full lap or track length (meters)"""
        length = ACC_TRACK_LENGTH(self.shmm.accStaticInfo.trackName)
        if length <= 0:
            length = self.udp.trackData.trackMeters
        return length

    def distance(self, index: int | None = None) -> float:
        """Distance into lap (meters)"""
        length = ACC_TRACK_LENGTH(self.shmm.accStaticInfo.trackName)
        if length <= 0:
            length = self.udp.trackData.trackMeters
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(length * self.shmm.accGraphicsInfo.normalizedCarPosition)
        return rmnan(length * self.udp_carinfo(index).splinePosition)

    def progress(self, index: int | None = None) -> float:
        """Lap progress (fraction), distance into lap"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accGraphicsInfo.normalizedCarPosition)
        return rmnan(self.udp_carinfo(index).splinePosition)

    def maximum(self) -> int:
        """Maximum lap"""
        return DATA.MAX_LAPS

    def remaining(self, index: int | None = None) -> float:
        """Remaining lap, count from current lap progress"""
        return 0.0

    def sector_index(self, index: int | None = None) -> int:
        """Sector index, 0 = S1, 1 = S2, 2 = S3"""
        sector = self.shmm.accLastSectorTime.index
        if sector == 0:
            return 0
        if sector == 1:
            return 1
        return 2

    def behind_leader(self, index: int | None = None) -> int:
        """Laps behind leader"""
        return 0.0

    def behind_next(self, index: int | None = None) -> int:
        """Laps behind next place"""
        return 0.0

    def safety_car_distance(self) -> float:
        """Safety car's distance into lap (meters)"""
        return 0.0

    def safety_car_active(self) -> bool:
        """Is safety car active on track"""
        return False


class Session(_reader.Session, DataAdapter):
    """Session"""

    __slots__ = ()

    def combo_name(self) -> str:
        """Track & vehicle combo name, strip off invalid char"""
        track_name = self.track_name()
        class_name = ACC_CAR_CLASS(self.shmm.accStaticInfo.carModel)
        return strip_invalid_char(f"{track_name} - {class_name}")

    def track_name(self) -> str:
        """Track name, strip off invalid char"""
        raw_name = self.shmm.accStaticInfo.trackName
        track_name = ACC_TRACK_NAME(raw_name)
        if track_name:
            track_year = ACC_TRACK_YEAR(raw_name)
            if track_year:
                track_name = f"{track_name} {track_year}"
        else:
            track_name = tostr(self.udp.trackData.trackName)
            if not track_name:
                track_name = raw_name.replace("_", " ").title()
        return strip_invalid_char(track_name)

    def identifier(self) -> tuple[int, int, int]:
        """Identify session"""
        session_type = self.shmm.accGraphicsInfo.session
        session_stamp = int(self.shmm.accGraphicsInfo.sessionIndex * 100 + session_type)
        session_etime = int(rmnan(90000 - self.shmm.accGraphicsInfo.sessionTimeLeft * 0.001))
        session_tlaps = self.shmm.accGraphicsInfo.numberOfLaps
        return session_stamp, session_etime, session_tlaps

    def elapsed(self) -> float:
        """Session elapsed time (seconds)"""
        return self.shmm.elapsed

    def start(self) -> float:
        """Session start time (seconds)"""
        return 0.0

    def end(self) -> float:
        """Session end time (seconds)"""
        return 0.0

    def remaining(self) -> float:
        """Session time remaining (seconds), minimum limit to 0"""
        seconds = self.shmm.accGraphicsInfo.sessionTimeLeft * 0.001
        if seconds < 0:
            seconds = 0.0
        return seconds

    def session_type(self) -> int:
        """Session type, 0 = TESTDAY, 1 = PRACTICE, 2 = QUALIFY, 3 = WARMUP, 4 = RACE, 5 = HOTLAP"""
        session = self.shmm.accGraphicsInfo.session
        if session == 2:  # race
            return 4
        if session == 1:  # qualify
            return 2
        if session == 0:  # practice
            return 1
        if session >= 3:  # hotlap
            return 5
        return 0  # test day

    def finish_type(self, as_lap: bool | None = None) -> int:
        """Race finish type, 0 = time, 1 = laps only, 2 = laps & time"""
        return 0  # time only in ACC

    def in_race(self) -> bool:
        """Is in race session"""
        return self.shmm.accGraphicsInfo.session == 2

    def private_qualifying(self) -> bool:
        """Is private qualifying"""
        return False

    def pit_open(self) -> bool:
        """Is pit lane open"""
        return True

    def pre_race(self) -> bool:
        """Before race starts (green flag)"""
        data = self.shmm.accGraphicsInfo
        return data.session == 2 and data.GlobalGreen <= 0

    def green_flag(self) -> bool:
        """Green flag (race starts)"""
        data = self.shmm.accGraphicsInfo
        return data.session == 2 and data.GlobalGreen > 0

    def blue_flag(self, index: int | None = None) -> bool:
        """Is under blue flag"""
        return self.shmm.accGraphicsInfo.flag == 1

    def yellow_flag(self) -> bool:
        """Is there yellow flag in any sectors"""
        return self.shmm.accGraphicsInfo.GlobalYellow

    def start_lights(self) -> int:
        """Start lights countdown sequence, 0=green flag"""
        data = self.shmm.accGraphicsInfo
        # Green flag check
        if data.completedLaps > 0 or data.GlobalGreen > 0:
            return 0
        # Start lights sequence
        return -1

    def track_temperature(self) -> float:
        """Track temperature (Celsius)"""
        return rmnan(self.shmm.accPhysicsInfo.roadTemp)

    def ambient_temperature(self) -> float:
        """Ambient temperature (Celsius)"""
        return rmnan(self.shmm.accPhysicsInfo.airTemp)

    def raininess(self) -> float:
        """Rain severity (fraction), range 0.0 - 1.0

        Rain in percent:
            0=none, 5=drizzle, 15=light rain, 30=medium rain, 60=heavy rain, 100=thunderstorm
        """
        raininess = self.shmm.accGraphicsInfo.rainIntensity
        if raininess == 0:
            return 0.0
        if raininess == 1:
            return 0.05
        if raininess == 2:
            return 0.15
        if raininess == 3:
            return 0.30
        if raininess == 4:
            return 0.60
        return 1.0

    def wetness(self) -> float:
        """Road wetness set (fraction), range 0.0 - 1.0

        Wetness in percent:
            0=none, 5=greasy, 10=damp, 15=wet, 60=flooded
        """
        wetness = self.shmm.accGraphicsInfo.trackGripStatus
        if wetness == 3:
            return 0.05
        if wetness == 4:
            return 0.1
        if wetness == 5:
            return 0.15
        if wetness == 6:
            return 0.60
        return 0.0

    def weather_forecast(self) -> tuple[tuple[float, int, float, float]]:
        """Weather forecast nodes, 0=forecast minutes, 1=sky type index, 2=air temperature, 3=rain chance"""
        data = self.shmm.accGraphicsInfo
        return (
            (10, ACC_TO_RF2_SKY_TYPE(data.rainIntensityIn10min), DATA.ABS_ZERO_CELSIUS, 0.0),
            (30, ACC_TO_RF2_SKY_TYPE(data.rainIntensityIn30min), DATA.ABS_ZERO_CELSIUS, 0.0),
        )

    def cloud_coverage(self) -> int:
        """Cloud coverage (type index), range 0 to 10

        Sky type:
            0 Clear, 1 Light Clouds, 2 Partially Cloudy, 3 Mostly Cloudy, 4 Overcast,
            5 Cloudy & Drizzle, 6 Cloudy & Light Rain, 7 Overcast & Light Rain,
            8 Overcast & Rain, 9 Overcast & Heavy Rain, 10 Overcast & Storm
        """
        return ACC_TO_RF2_SKY_TYPE(self.shmm.accGraphicsInfo.rainIntensity)

    def grip_level(self) -> float:
        """Track base grip level, convert to fraction 0.0 to 1.0"""
        grip = self.shmm.accGraphicsInfo.trackGripStatus
        if grip == 1:
            return 0.6
        if grip == 2:
            return 1.0
        return 0.0

    def track_time(self) -> float:
        """Track time"""
        return self.shmm.accGraphicsInfo.timeOfDay

    def time_scale(self) -> int:
        """Time scale"""
        return self.shmm.accTimeScale.scale

    def limits_points(self) -> float:
        """Track limits points per penalty"""
        return 0.0

    def cut_points(self, index: int | None = None) -> float:
        """Current track limits cut points per penalty"""
        return 0.0

    def wind_direction(self) -> float:
        """Wind direction (degrees)"""
        dir = rmnan(self.shmm.accGraphicsInfo.windDirection + 90)
        if dir == 0:
            return 0
        return dir - dir // 360 * 360

    def wind_speed(self) -> float:
        """Wind speed (m/s)"""
        return rmnan(self.shmm.accGraphicsInfo.windSpeed / 3.6)


class Switch(_reader.Switch, DataAdapter):
    """Switch"""

    __slots__ = ()

    def tc_level(self, index: int | None = None) -> int:
        """TC level"""
        return self.shmm.accGraphicsInfo.TC

    def tc_cut_level(self, index: int | None = None) -> int:
        """TC cut level"""
        return self.shmm.accGraphicsInfo.TCCUT

    def tc_slip_level(self, index: int | None = None) -> int:
        """TC slip level"""
        return -1

    def abs_level(self, index: int | None = None) -> int:
        """ABS level"""
        return self.shmm.accGraphicsInfo.ABS

    def motor_map_level(self, index: int | None = None) -> int:
        """Motor or engine map level"""
        return self.shmm.accGraphicsInfo.engineMap + 1

    def brake_migration_level(self, index: int | None = None) -> int:
        """Brake migration level"""
        return -1

    def front_arb_level(self, index: int | None = None) -> int:
        """Front anti-roll bar level"""
        return -1

    def rear_arb_level(self, index: int | None = None) -> int:
        """Rear anti-roll bar level"""
        return -1

    def wipers(self, index: int | None = None) -> int:
        """Wipers state, 0 = off, 1 = auto, 2 = slow, 3 = fast"""
        return self.shmm.accGraphicsInfo.wiperLV

    def headlights(self, index: int | None = None) -> int:
        """Headlights"""
        data = self.shmm.accGraphicsInfo
        if data.flashingLights:
            return self.shmm.elapsed % 1 * 4 // 1 % 2  # pulse every 0.25s
        return data.lightsStage

    def ignition_starter(self, index: int | None = None) -> int:
        """Ignition"""
        data = self.shmm.accPhysicsInfo
        if data.ignitionOn:
            if data.starterEngineOn:
                return 2
            return 1
        return 0

    def speed_limiter(self, index: int | None = None) -> int:
        """Speed limiter"""
        return self.shmm.accPhysicsInfo.pitLimiterOn

    def tc_active(self, index: int | None = None) -> bool:
        """TC activation state"""
        return self.shmm.accPhysicsInfo.tc > 0

    def abs_active(self, index: int | None = None) -> bool:
        """ABS activation state"""
        return self.shmm.accPhysicsInfo.abs > 0

    def drs_status(self, index: int | None = None) -> int:
        """DRS status, 0 not_available, 1 available, 2 allowed(not activated), 3 activated"""
        return 0

    def auto_clutch(self) -> bool:
        """Auto clutch"""
        return self.shmm.accStaticInfo.aidAutoClutch > 0


class Timing(_reader.Timing, DataAdapter):
    """Timing"""

    __slots__ = ()

    def elapsed(self, index: int | None = None) -> float:
        """Current elapsed time (seconds)"""
        return self.shmm.elapsed

    def is_last_valid(self, index: int | None = None) -> bool:
        """Is last lap time valid"""
        if index is None:  # or index == self.shmm.playerIndex:
            return self.shmm.accValidLap.last
        return not self.udp_carinfo(index).lastLap.isInvalid

    def current_laptime(self, index: int | None = None) -> float:
        """Current lap time (seconds)"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accGraphicsInfo.iCurrentTime * 0.001)
        return self.udp_carinfo(index).currentLap.laptimeMS * 0.001

    def last_laptime(self, index: int | None = None) -> float:
        """Last lap time (seconds), positive=valid, negative=invalid"""
        if index is None:  # or index == self.shmm.playerIndex:
            last = rmnan(self.shmm.accGraphicsInfo.iLastTime * 0.001)
            if self.shmm.accValidLap.last:
                return last
            return -last
        data = self.udp_carinfo(index)
        last = data.lastLap.laptimeMS * 0.001
        if data.lastLap.isInvalid:
            return -last
        return last

    def best_laptime(self, index: int | None = None) -> float:
        """Best lap time (seconds)"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accGraphicsInfo.iBestTime * 0.001)
        return self.udp_carinfo(index).bestSessionLap.laptimeMS * 0.001

    def reference_laptime(self, index: int | None = None, laptime: float = 0) -> float:
        """Reference lap time (seconds)"""
        if 0 < laptime < DATA.MAX_SECONDS:
            return laptime
        init_time = min_nonzero((
            self.best_laptime(index),
            self.last_laptime(index),
            DATA.MAX_SECONDS,
        ))
        if 0 < init_time < DATA.MAX_SECONDS:
            return init_time
        # Set to estimated laptime only if other laptime not available
        # as estimated laptime can be faster than other laptime
        return min_nonzero((
            self.estimated_laptime(index),
            DATA.MAX_SECONDS,
        ))

    def estimated_laptime(self, index: int | None = None) -> float:
        """Estimated lap time (seconds)"""
        length = ACC_TRACK_LENGTH(self.shmm.accStaticInfo.trackName)
        if length <= 0:
            length = self.udp.trackData.trackMeters
        return length / 40

    def estimated_time_into(self, index: int | None = None) -> float:
        """Estimated time into lap (seconds)"""
        length = ACC_TRACK_LENGTH(self.shmm.accStaticInfo.trackName)
        if length <= 0:
            length = self.udp.trackData.trackMeters
        estimated_laptime = length / 40
        if index is None:
            index = self.shmm.playerIndex
            #return rmnan(estimated_laptime * self.shmm.accGraphicsInfo.normalizedCarPosition)
        return rmnan(estimated_laptime * self.udp_carinfo(index).splinePosition)

    def last_sector(self, index: int | None = None) -> float:
        """Last sector time (seconds)"""
        return self.shmm.accLastSectorTime.last

    def behind_leader(self, index: int | None = None) -> float:
        """Time behind leader (seconds)"""
        return 0.0

    def behind_next(self, index: int | None = None) -> float:
        """Time behind next place (seconds)"""
        return 0.0


class Tyre(_reader.Tyre, DataAdapter):
    """Tyre (front left, front right, rear left, rear right)"""

    __slots__ = ()

    def compound_name(self, index: int | None = None) -> tuple[str, ...]:
        """Tyre compound name set"""
        if index is None:  # or index == self.shmm.playerIndex:
            compound = self.shmm.accGraphicsInfo.tyreCompound.replace("_", " ").title()
            return compound, compound, compound, compound
        return "", "", "", ""

    def compound_class(self, index: int | None = None) -> tuple[str, ...]:
        """Tyre compound name set with class name prefix"""
        if index is None:  # or index == self.shmm.playerIndex:
            compound = self.shmm.accGraphicsInfo.tyreCompound.replace("_", " ").title()
            class_name = ACC_CAR_CLASS(self.shmm.accStaticInfo.carModel)
            tyre_name = f"{class_name} - {compound}"
            return tyre_name, tyre_name, tyre_name, tyre_name
        return "", "", "", ""

    def surface_temperature_avg(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) average"""
        data = self.shmm.accPhysicsInfo.tyreTemp
        return (
            rmnan(data[0]),
            rmnan(data[1]),
            rmnan(data[2]),
            rmnan(data[3]),
        )

    def surface_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) inner,center,outer"""
        data = self.shmm.accPhysicsInfo.tyreTemp
        front_left = rmnan(data[0])
        front_right = rmnan(data[0])
        rear_left = rmnan(data[0])
        rear_right = rmnan(data[0])
        return (
            front_left, front_left, front_left,
            front_right, front_right, front_right,
            rear_left, rear_left, rear_left,
            rear_right, rear_right, rear_right,
        )

    def inner_temperature_avg(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre inner temperature set (Celsius) average"""
        surface = self.shmm.accPhysicsInfo.tyreTemp
        core = self.shmm.accPhysicsInfo.tyreCoreTemp
        return (
            rmnan((surface[0] + core[0]) / 2),
            rmnan((surface[1] + core[1]) / 2),
            rmnan((surface[2] + core[2]) / 2),
            rmnan((surface[3] + core[3]) / 2),
        )

    def inner_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre inner temperature set (Celsius) inner,center,outer"""
        surface = self.shmm.accPhysicsInfo.tyreTemp
        core = self.shmm.accPhysicsInfo.tyreCoreTemp
        front_left = rmnan((surface[0] + core[0]) / 2)
        front_right = rmnan((surface[1] + core[1]) / 2)
        rear_left = rmnan((surface[2] + core[2]) / 2)
        rear_right = rmnan((surface[3] + core[3]) / 2)
        return (
            front_left, front_left, front_left,
            front_right, front_right, front_right,
            rear_left, rear_left, rear_left,
            rear_right, rear_right, rear_right,
        )

    def pressure(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre pressure (kPa)"""
        data = self.shmm.accPhysicsInfo.wheelPressure
        return (
            rmnan(data[0] * 6.89475729),  # psi to kPa
            rmnan(data[1] * 6.89475729),
            rmnan(data[2] * 6.89475729),
            rmnan(data[3] * 6.89475729),
        )

    def load(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre load (Newtons)"""
        return DATA.WHEELS_ZERO

    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre wear (fraction)"""
        return DATA.WHEELS_NA

    def puncture(self, index: int | None = None, threshold: float = 1) -> tuple[bool, ...]:
        """Tyre puncture state"""
        data = self.shmm.accPhysicsInfo.wheelPressure
        return (
            data[0] <= threshold,
            data[1] <= threshold,
            data[2] <= threshold,
            data[3] <= threshold,
        )

    def carcass_temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre carcass temperature (Celsius)"""
        data = self.shmm.accPhysicsInfo.tyreCoreTemp
        return (
            rmnan(data[0]),
            rmnan(data[1]),
            rmnan(data[2]),
            rmnan(data[3]),
        )

    def vertical_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre vertical deflection (millimeters)"""
        return 1, 1, 1, 1

    def slip_angle(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre slip angle (radians)"""
        data = self.shmm.accPhysicsInfo.slipAngle
        return (
            rmnan(data[0]),
            rmnan(data[1]),
            rmnan(data[2]),
            rmnan(data[3]),
        )


class Vehicle(_reader.Vehicle, DataAdapter):
    """Vehicle"""

    __slots__ = ()

    def incidents(self, index: int | None = None) -> int:
        """Number of incidents"""
        return 0.0

    def is_player(self, index: int = 0) -> bool:
        """Is local player"""
        return self.shmm.playerIndex == index

    def is_driving(self) -> bool:
        """Is local player driving or in monitor"""
        return self.shmm.accPhysicsInfo.currentMaxRPM > 0

    def player_index(self) -> int:
        """Get Local player index"""
        return self.shmm.playerIndex

    def slot_id(self, index: int | None = None) -> int:
        """Vehicle slot id"""
        if index is None:
            index = self.shmm.playerIndex
        return self.shmm.accGraphicsInfo.carIDs[index]

    def driver_name(self, index: int | None = None) -> str:
        """Driver name"""
        if index is None:  # or index == self.shmm.playerIndex:
            stat_info = self.shmm.accStaticInfo
            return f"{stat_info.playerName} {stat_info.playerSurname}"
        data = self.udp_carinfo(index).currentDriverInfo
        return f"{tostr(data.firstName)} {tostr(data.lastName)}"

    def team_name(self, index: int | None = None) -> str:
        """Team name"""
        if index is None:
            index = self.shmm.playerIndex
        return tostr(self.udp_carinfo(index).teamName)

    def vehicle_model(self, index: int | None = None) -> str:
        """Vehicle model name (brand name + model ID)"""
        if index is None:  # or index == self.shmm.playerIndex:
            model = self.shmm.accStaticInfo.carModel
            model_name = ACC_CAR_MODEL(model)
            if model_name:
                return model_name
            return model.replace("_", " ").title()
        model = ACC_CAR_MODEL_ID(self.udp_carinfo(index).carModelType)
        model_name = ACC_CAR_MODEL(model)
        if model_name:
            return model_name
        return "Unknown"

    def class_name(self, index: int | None = None) -> str:
        """Vehicle class name"""
        if index is None:  # or index == self.shmm.playerIndex:
            return ACC_CAR_CLASS(self.shmm.accStaticInfo.carModel)
        model = ACC_CAR_MODEL_ID(self.udp_carinfo(index).carModelType)
        return ACC_CAR_CLASS(model)

    def same_class(self, index: int | None = None) -> bool:
        """Is same vehicle class"""
        player_class = ACC_CAR_CLASS(ACC_CAR_MODEL_ID(self.udp_carinfo(self.shmm.playerIndex).carModelType))
        opponent_class = ACC_CAR_CLASS(ACC_CAR_MODEL_ID(self.udp_carinfo(index).carModelType))
        return opponent_class == player_class

    def total_vehicles(self) -> int:
        """Total vehicles"""
        return self.shmm.accGraphicsInfo.activeCars

    def place(self, index: int | None = None) -> int:
        """Vehicle overall place"""
        if index is None:  # or index == self.shmm.playerIndex:
            return self.shmm.accGraphicsInfo.position
        return self.udp_carinfo(index).position

    def qualification(self, index: int | None = None) -> int:
        """Vehicle qualification place"""
        return 0

    def in_pits(self, index: int | None = None) -> bool:
        """Is in pits"""
        if index is None:  # or index == self.shmm.playerIndex:
            return self.shmm.accGraphicsInfo.isInPitLane > 0
        return self.udp_carinfo(index).carLocation >= 2

    def in_garage(self, index: int | None = None) -> bool:
        """Is in garage"""
        if index is None:  # or index == self.shmm.playerIndex:
            return (
                self.shmm.accGraphicsInfo.isInPitLane > 0
                and self.shmm.accVehicleSpeed(index) <= 0
            )
        data = self.udp_carinfo(index)
        return data.carLocation >= 2 and data.speedKmh <= 0

    def in_paddock(self, index: int | None = None) -> int:
        """Is in paddock (either pit lane or garage), 0 = on track, 1 = pit lane, 2 = garage"""
        if index is None:  # or index == self.shmm.playerIndex:
            in_pit = self.shmm.accGraphicsInfo.isInPitLane > 0
            stopped = self.shmm.accVehicleSpeed(index) <= 0
        else:
            data = self.udp_carinfo(index)
            in_pit = data.carLocation >= 2
            stopped = data.speedKmh <= 0
        return 2 if in_pit and stopped else in_pit

    def number_pitstops(self, index: int | None = None, penalty: int = 0) -> int:
        """Number of pit stops"""
        if index is None:  # or index == self.shmm.playerIndex:
            data = self.shmm.accGraphicsInfo
            return -penalty if penalty else data.mandatoryPitDone
        return 0

    def number_penalties(self, index: int | None = None) -> int:
        """Number of penalties"""
        if index is None:  # or index == self.shmm.playerIndex:
            return self.shmm.accGraphicsInfo.penalty > 0
        return 0

    def pit_request(self, index: int | None = None) -> bool:
        """Is requested pit, 0 = none, 1 = request, 2 = entering, 3 = stopped, 4 = exiting"""
        return 0

    def pit_stop_time(self) -> float:
        """Estimated pit stop time (seconds)"""
        return 0.0

    def repair_time(self) -> float:
        """Scheduled repair time (seconds)"""
        return 0.0

    def finish_state(self, index: int | None = None) -> int:
        """Finish state, 0 = none, 1 = finished, 2 = DNF, 3 = DQ"""
        if index is None:  # or index == self.shmm.playerIndex:
            state = self.shmm.accGraphicsInfo.flag
            if state == 0:
                return 0
            if state == 5:
                return 1
            if state == 3:
                return 3
            return 0
        return 0

    def orientation_yaw(self, index: int | None = None) -> float:
        """Orientation yaw (radians)"""
        if index is None:
            return rmnan(-self.shmm.accPhysicsInfo.heading)
        if self.shmm.accVehicleSpeed(index) < 3:  # only for stationary yaw
            return rmnan(-self.udp_carinfo(index).yaw)  # low update rate data
        return rmnan(self.shmm.accVehicleYaw(index))  # high precision only while moving

    def position_xyz(self, index: int | None = None) -> tuple[float, float, float]:
        """Raw x,y,z position (meters)"""
        if index is None:
            index = self.shmm.playerIndex
        pos = self.shmm.accGraphicsInfo.carCoordinates[index]
        return rmnan(pos.x), rmnan(pos.y), rmnan(pos.z)

    def position_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal axis position (meters) related to world plane"""
        if index is None:
            index = self.shmm.playerIndex
        pos = self.shmm.accGraphicsInfo.carCoordinates[index]
        return rmnan(pos.x)  # in ACC coord system

    def position_lateral(self, index: int | None = None) -> float:
        """Lateral axis position (meters) related to world plane"""
        if index is None:
            index = self.shmm.playerIndex
        pos = self.shmm.accGraphicsInfo.carCoordinates[index]
        return rmnan(pos.z)  # in ACC coord system

    def position_vertical(self, index: int | None = None) -> float:
        """Vertical axis position (meters) related to world plane"""
        if index is None:
            index = self.shmm.playerIndex
        pos = self.shmm.accGraphicsInfo.carCoordinates[index]
        return rmnan(pos.y)  # in ACC coord system

    def acceleration_lateral(self, index: int | None = None) -> float:
        """Lateral acceleration (m/s^2)"""
        return rmnan(self.shmm.accPhysicsInfo.acceleration.x * 9.8)  # X in ACC coord system

    def acceleration_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal acceleration (m/s^2)"""
        return rmnan(-self.shmm.accPhysicsInfo.acceleration.z * 9.8)  # Z in ACC coord system

    def acceleration_vertical(self, index: int | None = None) -> float:
        """Vertical acceleration (m/s^2)"""
        return rmnan(self.shmm.accPhysicsInfo.acceleration.y * 9.8)  # Y in ACC coord system

    def velocity_lateral(self, index: int | None = None) -> float:
        """Lateral velocity (m/s) x"""
        return rmnan(self.shmm.accPhysicsInfo.velocity.x)  # X in ACC coord system

    def velocity_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal velocity (m/s) y"""
        return rmnan(self.shmm.accPhysicsInfo.velocity.z)  # Z in ACC coord system

    def velocity_vertical(self, index: int | None = None) -> float:
        """Vertical velocity (m/s) z"""
        return rmnan(self.shmm.accPhysicsInfo.velocity.y)  # Y in ACC coord system

    def speed(self, index: int | None = None) -> float:
        """Speed (m/s)"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(self.shmm.accPhysicsInfo.speedKmh / 3.6)
        return self.shmm.accVehicleSpeed(index)

    def downforce_front(self, index: int | None = None) -> float:
        """Downforce front (Newtons)"""
        return 0.0

    def downforce_rear(self, index: int | None = None) -> float:
        """Downforce rear (Newtons)"""
        return 0.0

    def damage_severity(self, index: int | None = None) -> tuple[int, int, int, int, int, int, int, int]:
        """Damage severity, sort row by row from left to right, top to bottom"""
        # ACC order: front 0, rear 1, left 2, right 3, center 4
        # 0-50=light damage, 50+=heavy damage
        data = self.shmm.accPhysicsInfo.carDamage
        front = rmnan(data[0] * 0.02)
        rear = rmnan(data[1] * 0.02)
        left = rmnan(data[2] * 0.02)
        right = rmnan(data[3] * 0.02)
        front_left = front * left / 4
        front_right = front * right / 4
        rear_left = rear * left / 4
        rear_right = rear * right / 4
        return (
            front_left, front, front_right,
            left,                    right,
            rear_left,  rear,   rear_right,
        )

    def aero_damage(self, index: int | None = None) -> float:
        """Aerodynamic damage (fraction), -1.0 unavailable, 0.0 no damage, 1.0 totaled"""
        return -1.0

    def integrity(self, index: int | None = None) -> float:
        """Vehicle integrity"""
        if index is None:  # or index == self.shmm.playerIndex:
            return rmnan(1 - self.shmm.accPhysicsInfo.carDamage[4] / 400)
        return 1.0

    def is_detached(self, index: int | None = None) -> bool:
        """Whether any vehicle parts are detached"""
        return False

    def impact_time(self, index: int | None = None) -> float:
        """Last impact time stamp (seconds)"""
        return self.shmm.accLastImpact.timestamp

    def impact_position(self, index: int | None = None) -> tuple[float, float]:
        """Last impact position x,y coordinates"""
        return self.shmm.accLastImpact.position

    def setup(self) -> tuple[str, ...]:
        """Car setup data"""
        return ()


class Wheel(_reader.Wheel, DataAdapter):
    """Wheel & suspension (front left, front right, rear left, rear right)"""

    __slots__ = ()

    def camber(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel camber (radians)"""
        return DATA.WHEELS_ZERO

    def toe(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel toe (radians)"""
        data = self.shmm.accPhysicsInfo.tyreContactHeading
        yaw = self.shmm.accPhysicsInfo.heading
        ph = pi * 0.5
        if ph > yaw > -ph:
            return (
                rmnan(-yaw - atan2(-data[0].x, -data[0].z)),
                rmnan(-yaw - atan2(-data[1].x, -data[1].z)),
                rmnan(-yaw - atan2(-data[2].x, -data[2].z)),
                rmnan(-yaw - atan2(-data[3].x, -data[3].z)),
            )
        if yaw < 0:
            yaw = -pi - yaw
        elif yaw > 0:
            yaw = pi - yaw
        return (
            rmnan(yaw - atan2(data[0].x, data[0].z)),
            rmnan(yaw - atan2(data[1].x, data[1].z)),
            rmnan(yaw - atan2(data[2].x, data[2].z)),
            rmnan(yaw - atan2(data[3].x, data[3].z)),
        )

    def rotation(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel rotation (radians per second), or angular velocity"""
        data = self.shmm.accPhysicsInfo.wheelAngularSpeed
        return (
            rmnan(-data[0]),
            rmnan(-data[1]),
            rmnan(-data[2]),
            rmnan(-data[3]),
        )

    def ride_height(self, index: int | None = None) -> tuple[float, ...]:
        """Ride height (convert meters to millimeters)"""
        return DATA.WHEELS_ZERO

    def third_spring_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Third spring deflection front & rear (convert meters to millimeters)"""
        data = self.shmm.accPhysicsInfo.suspensionTravel
        front = rmnan((data[0] + data[1]) * 500)
        rear = rmnan((data[2] + data[3]) * 500)
        return front, front, rear, rear

    def suspension_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension deflection (convert meters to millimeters)"""
        data = self.shmm.accPhysicsInfo.suspensionTravel
        return (
            rmnan(data[0]) * 1000,
            rmnan(data[1]) * 1000,
            rmnan(data[2]) * 1000,
            rmnan(data[3]) * 1000,
        )

    def suspension_force(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension force (Newtons)"""
        return DATA.WHEELS_ZERO

    def suspension_damage(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension damage (fraction), 0.0 no damage, 1.0 totaled"""
        data = self.shmm.accPhysicsInfo.suspensionDamage
        return (
            rmnan(data[0]),
            rmnan(data[1]),
            rmnan(data[2]),
            rmnan(data[3]),
        )

    def position_vertical(self, index: int | None = None) -> tuple[float, ...]:
        """Vertical wheel position (convert meters to millimeters) related to vehicle"""
        return DATA.WHEELS_ZERO

    def is_detached(self, index: int | None = None) -> tuple[bool, ...]:
        """Whether wheel is detached"""
        return DATA.WHEELS_ZERO

    def offroad(self, index: int | None = None) -> int:
        """Number of wheels currently off the road"""
        return False
