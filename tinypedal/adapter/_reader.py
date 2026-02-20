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
API data reader (abstract class)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..process.weather import WeatherNode


class State(ABC):
    """State"""

    __slots__ = ()

    @abstractmethod
    def active(self) -> bool:
        """Is active (driving or overriding)"""

    @abstractmethod
    def paused(self) -> bool:
        """Is paused"""

    @abstractmethod
    def desynced(self, index: int | None = None) -> bool:
        """Is player data desynced from others"""

    @abstractmethod
    def version(self) -> str:
        """Identify API version"""


class Brake(ABC):
    """Brake"""

    __slots__ = ()

    @abstractmethod
    def bias_front(self, index: int | None = None) -> float:
        """Brake bias front (fraction)"""

    @abstractmethod
    def pressure(self, index: int | None = None, scale: float = 1) -> tuple[float, ...]:
        """Brake pressure (fraction)"""

    @abstractmethod
    def temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Brake temperature (Celsius)"""

    @abstractmethod
    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Brake remaining thickness (meters)"""


class ElectricMotor(ABC):
    """Electric motor"""

    __slots__ = ()

    @abstractmethod
    def state(self, index: int | None = None) -> int:
        """Motor state, 0 = n/a, 1 = off, 2 = drain, 3 = regen"""

    @abstractmethod
    def battery_charge(self, index: int | None = None) -> float:
        """Battery charge (fraction)"""

    @abstractmethod
    def rpm(self, index: int | None = None) -> float:
        """Motor RPM (rev per minute)"""

    @abstractmethod
    def torque(self, index: int | None = None) -> float:
        """Motor torque (Nm)"""

    @abstractmethod
    def motor_temperature(self, index: int | None = None) -> float:
        """Motor temperature (Celsius)"""

    @abstractmethod
    def water_temperature(self, index: int | None = None) -> float:
        """Motor water temperature (Celsius)"""


class Engine(ABC):
    """Engine"""

    __slots__ = ()

    @abstractmethod
    def gear(self, index: int | None = None) -> int:
        """Gear"""

    @abstractmethod
    def gear_max(self, index: int | None = None) -> int:
        """Max gear"""

    @abstractmethod
    def rpm(self, index: int | None = None) -> float:
        """RPM (rev per minute)"""

    @abstractmethod
    def rpm_max(self, index: int | None = None) -> float:
        """Max RPM (rev per minute)"""

    @abstractmethod
    def torque(self, index: int | None = None) -> float:
        """Torque (Nm)"""

    @abstractmethod
    def turbo(self, index: int | None = None) -> float:
        """Turbo pressure (Pa)"""

    @abstractmethod
    def oil_temperature(self, index: int | None = None) -> float:
        """Oil temperature (Celsius)"""

    @abstractmethod
    def water_temperature(self, index: int | None = None) -> float:
        """Water temperature (Celsius)"""


class Inputs(ABC):
    """Inputs"""

    __slots__ = ()

    @abstractmethod
    def throttle(self, index: int | None = None) -> float:
        """Throttle filtered (fraction)"""

    @abstractmethod
    def throttle_raw(self, index: int | None = None) -> float:
        """Throttle raw (fraction)"""

    @abstractmethod
    def brake(self, index: int | None = None) -> float:
        """Brake filtered (fraction)"""

    @abstractmethod
    def brake_raw(self, index: int | None = None) -> float:
        """Brake raw (fraction)"""

    @abstractmethod
    def clutch(self, index: int | None = None) -> float:
        """Clutch filtered (fraction)"""

    @abstractmethod
    def clutch_raw(self, index: int | None = None) -> float:
        """Clutch raw (fraction)"""

    @abstractmethod
    def steering(self, index: int | None = None) -> float:
        """Steering filtered (fraction)"""

    @abstractmethod
    def steering_raw(self, index: int | None = None) -> float:
        """Steering raw (fraction)"""

    @abstractmethod
    def steering_shaft_torque(self, index: int | None = None) -> float:
        """Steering shaft torque (Nm)"""

    @abstractmethod
    def steering_range_physical(self, index: int | None = None) -> float:
        """Steering physical rotation range (degrees)"""

    @abstractmethod
    def steering_range_visual(self, index: int | None = None) -> float:
        """Steering visual rotation range (degrees)"""

    @abstractmethod
    def force_feedback(self) -> float:
        """Steering force feedback (fraction)"""


class Lap(ABC):
    """Lap"""

    __slots__ = ()

    @abstractmethod
    def number(self, index: int | None = None) -> int:
        """Current lap number"""

    @abstractmethod
    def completed_laps(self, index: int | None = None) -> int:
        """Total completed laps"""

    @abstractmethod
    def track_length(self) -> float:
        """Full lap or track length (meters)"""

    @abstractmethod
    def distance(self, index: int | None = None) -> float:
        """Distance into lap (meters)"""

    @abstractmethod
    def progress(self, index: int | None = None) -> float:
        """Lap progress (fraction), distance into lap"""

    @abstractmethod
    def maximum(self) -> int:
        """Maximum lap"""

    @abstractmethod
    def sector_index(self, index: int | None = None) -> int:
        """Sector index, 0 = S1, 1 = S2, 2 = S3"""

    @abstractmethod
    def behind_leader(self, index: int | None = None) -> int:
        """Laps behind leader"""

    @abstractmethod
    def behind_next(self, index: int | None = None) -> int:
        """Laps behind next place"""


class Session(ABC):
    """Session"""

    __slots__ = ()

    @abstractmethod
    def combo_name(self) -> str:
        """Track & vehicle combo name, strip off invalid char"""

    @abstractmethod
    def track_name(self) -> str:
        """Track name, strip off invalid char"""

    @abstractmethod
    def identifier(self) -> tuple[int, int, int]:
        """Identify session"""

    @abstractmethod
    def elapsed(self) -> float:
        """Session elapsed time (seconds)"""

    @abstractmethod
    def start(self) -> float:
        """Session start time (seconds)"""

    @abstractmethod
    def end(self) -> float:
        """Session end time (seconds)"""

    @abstractmethod
    def remaining(self) -> float:
        """Session time remaining (seconds)"""

    @abstractmethod
    def session_type(self) -> int:
        """Session type, 0 = TESTDAY, 1 = PRACTICE, 2 = QUALIFY, 3 = WARMUP, 4 = RACE"""

    @abstractmethod
    def lap_type(self) -> bool:
        """Is lap type session, false for time type"""

    @abstractmethod
    def in_race(self) -> bool:
        """Is in race session"""

    @abstractmethod
    def private_qualifying(self) -> bool:
        """Is private qualifying"""

    @abstractmethod
    def pit_open(self) -> bool:
        """Is pit lane open"""

    @abstractmethod
    def pre_race(self) -> bool:
        """Before race starts (green flag)"""

    @abstractmethod
    def green_flag(self) -> bool:
        """Green flag (race starts)"""

    @abstractmethod
    def blue_flag(self, index: int | None = None) -> bool:
        """Is under blue flag"""

    @abstractmethod
    def yellow_flag(self) -> bool:
        """Is there yellow flag in any sectors"""

    @abstractmethod
    def start_lights(self) -> int:
        """Start lights countdown sequence, 0=green flag"""

    @abstractmethod
    def track_temperature(self) -> float:
        """Track temperature (Celsius)"""

    @abstractmethod
    def ambient_temperature(self) -> float:
        """Ambient temperature (Celsius)"""

    @abstractmethod
    def raininess(self) -> float:
        """Rain severity (fraction)"""

    @abstractmethod
    def wetness_minimum(self) -> float:
        """Road minimum wetness (fraction)"""

    @abstractmethod
    def wetness_maximum(self) -> float:
        """Road maximum wetness (fraction)"""

    @abstractmethod
    def wetness_average(self) -> float:
        """Road average wetness (fraction)"""

    @abstractmethod
    def wetness(self) -> tuple[float, float, float]:
        """Road wetness set (fraction)"""

    @abstractmethod
    def weather_forecast(self) -> tuple[WeatherNode, ...]:
        """Weather forecast nodes"""

    @abstractmethod
    def track_time(self) -> float:
        """Track time"""

    @abstractmethod
    def time_scale(self) -> int:
        """Time scale"""


class Switch(ABC):
    """Switch"""

    __slots__ = ()

    @abstractmethod
    def headlights(self, index: int | None = None) -> int:
        """Headlights"""

    @abstractmethod
    def ignition_starter(self, index: int | None = None) -> int:
        """Ignition"""

    @abstractmethod
    def speed_limiter(self, index: int | None = None) -> int:
        """Speed limiter"""

    @abstractmethod
    def drs_status(self, index: int | None = None) -> int:
        """DRS status, 0 not_available, 1 available, 2 allowed(not activated), 3 activated"""

    @abstractmethod
    def auto_clutch(self) -> bool:
        """Auto clutch"""


class Timing(ABC):
    """Timing"""

    __slots__ = ()

    @abstractmethod
    def start(self, index: int | None = None) -> float:
        """Current lap start time (seconds)"""

    @abstractmethod
    def elapsed(self, index: int | None = None) -> float:
        """Current lap elapsed time (seconds)"""

    @abstractmethod
    def current_laptime(self, index: int | None = None) -> float:
        """Current lap time (seconds)"""

    @abstractmethod
    def last_laptime(self, index: int | None = None) -> float:
        """Last lap time (seconds)"""

    @abstractmethod
    def best_laptime(self, index: int | None = None) -> float:
        """Best lap time (seconds)"""

    @abstractmethod
    def reference_laptime(self, index: int | None = None):
        """Reference lap time (seconds)"""

    @abstractmethod
    def estimated_laptime(self, index: int | None = None) -> float:
        """Estimated lap time (seconds)"""

    @abstractmethod
    def estimated_time_into(self, index: int | None = None) -> float:
        """Estimated time into lap (seconds)"""

    @abstractmethod
    def current_sector1(self, index: int | None = None) -> float:
        """Current lap sector 1 time (seconds)"""

    @abstractmethod
    def current_sector2(self, index: int | None = None) -> float:
        """Current lap sector 1+2 time (seconds)"""

    @abstractmethod
    def last_sector1(self, index: int | None = None) -> float:
        """Last lap sector 1 time (seconds)"""

    @abstractmethod
    def last_sector2(self, index: int | None = None) -> float:
        """Last lap sector 1+2 time (seconds)"""

    @abstractmethod
    def best_sector1(self, index: int | None = None) -> float:
        """Best lap sector 1 time (seconds)"""

    @abstractmethod
    def best_sector2(self, index: int | None = None) -> float:
        """Best lap sector 1+2 time (seconds)"""

    @abstractmethod
    def behind_leader(self, index: int | None = None) -> float:
        """Time behind leader (seconds)"""

    @abstractmethod
    def behind_next(self, index: int | None = None) -> float:
        """Time behind next place (seconds)"""


class Tyre(ABC):
    """Tyre"""

    __slots__ = ()

    @abstractmethod
    def compound_front(self, index: int | None = None) -> int:
        """Tyre compound (front)"""

    @abstractmethod
    def compound_rear(self, index: int | None = None) -> int:
        """Tyre compound (rear)"""

    @abstractmethod
    def compound(self, index: int | None = None) -> tuple[int, int]:
        """Tyre compound set (front, rear)"""

    @abstractmethod
    def compound_name_front(self, index: int | None = None) -> str:
        """Tyre compound name (front)"""

    @abstractmethod
    def compound_name_rear(self, index: int | None = None) -> str:
        """Tyre compound name (rear)"""

    @abstractmethod
    def compound_name(self, index: int | None = None) -> tuple[str, str]:
        """Tyre compound name set (front, rear)"""

    @abstractmethod
    def surface_temperature_avg(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) average"""

    @abstractmethod
    def surface_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre surface temperature set (Celsius) inner,center,outer"""

    @abstractmethod
    def inner_temperature_avg(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre inner temperature set (Celsius) average"""

    @abstractmethod
    def inner_temperature_ico(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre inner temperature set (Celsius) inner,center,outer"""

    @abstractmethod
    def pressure(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre pressure (kPa)"""

    @abstractmethod
    def load(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre load (Newtons)"""

    @abstractmethod
    def wear(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre wear (fraction)"""

    @abstractmethod
    def carcass_temperature(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre carcass temperature (Celsius)"""

    @abstractmethod
    def vertical_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Tyre vertical deflection (millimeters)"""


class Vehicle(ABC):
    """Vehicle"""

    __slots__ = ()

    @abstractmethod
    def is_player(self, index: int=0) -> bool:
        """Is local player"""

    @abstractmethod
    def is_driving(self) -> bool:
        """Is local player driving or in monitor"""

    @abstractmethod
    def player_index(self) -> int:
        """Get Local player index"""

    @abstractmethod
    def slot_id(self, index: int | None = None) -> int:
        """Vehicle slot id"""

    @abstractmethod
    def driver_name(self, index: int | None = None) -> str:
        """Driver name"""

    @abstractmethod
    def vehicle_name(self, index: int | None = None) -> str:
        """Vehicle name"""

    @abstractmethod
    def class_name(self, index: int | None = None) -> str:
        """Vehicle class name"""

    @abstractmethod
    def same_class(self, index: int | None = None) -> bool:
        """Is same vehicle class"""

    @abstractmethod
    def total_vehicles(self) -> int:
        """Total vehicles"""

    @abstractmethod
    def place(self, index: int | None = None) -> int:
        """Vehicle overall place"""

    @abstractmethod
    def qualification(self, index: int | None = None) -> int:
        """Vehicle qualification place"""

    @abstractmethod
    def in_pits(self, index: int | None = None) -> bool:
        """Is in pits"""

    @abstractmethod
    def in_garage(self, index: int | None = None) -> bool:
        """Is in garage"""

    @abstractmethod
    def in_paddock(self, index: int | None = None) -> int:
        """Is in paddock (either pit lane or garage), 0 = on track, 1 = pit lane, 2 = garage"""

    @abstractmethod
    def number_pitstops(self, index: int | None = None, penalty: int = 0) -> int:
        """Number of pit stops"""

    @abstractmethod
    def number_penalties(self, index: int | None = None) -> int:
        """Number of penalties"""

    @abstractmethod
    def pit_request(self, index: int | None = None) -> bool:
        """Is requested pit, 0 = none, 1 = request, 2 = entering, 3 = stopped, 4 = exiting"""

    @abstractmethod
    def pit_stop_time(self) -> float:
        """Estimated pit stop time (seconds)"""

    @abstractmethod
    def absolute_refill(self) -> float:
        """Absolute refill fuel (liter) or virtual energy (percent)"""

    @abstractmethod
    def stint_usage(self, driver_name: str) -> tuple[float, float, float, float, int]:
        """Stint usage data"""

    @abstractmethod
    def finish_state(self, index: int | None = None) -> int:
        """Finish state, 0 = none, 1 = finished, 2 = DNF, 3 = DQ"""

    @abstractmethod
    def fuel(self, index: int | None = None) -> float:
        """Remaining fuel (liters)"""

    @abstractmethod
    def tank_capacity(self, index: int | None = None) -> float:
        """Fuel tank capacity (liters)"""

    @abstractmethod
    def virtual_energy(self, index: int | None = None) -> float:
        """Remaining virtual energy (joule)"""

    @abstractmethod
    def max_virtual_energy(self, index: int | None = None) -> float:
        """Max virtual energy (joule)"""

    @abstractmethod
    def orientation_yaw_radians(self, index: int | None = None) -> float:
        """Orientation yaw (radians)"""

    @abstractmethod
    def position_xyz(self, index: int | None = None) -> tuple[float, float, float]:
        """Raw x,y,z position (meters)"""

    @abstractmethod
    def position_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal axis position (meters) related to world plane"""

    @abstractmethod
    def position_lateral(self, index: int | None = None) -> float:
        """Lateral axis position (meters) related to world plane"""

    @abstractmethod
    def position_vertical(self, index: int | None = None) -> float:
        """Vertical axis position (meters) related to world plane"""

    @abstractmethod
    def accel_lateral(self, index: int | None = None) -> float:
        """Lateral acceleration (m/s^2)"""

    @abstractmethod
    def accel_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal acceleration (m/s^2)"""

    @abstractmethod
    def accel_vertical(self, index: int | None = None) -> float:
        """Vertical acceleration (m/s^2)"""

    @abstractmethod
    def velocity_lateral(self, index: int | None = None) -> float:
        """Lateral velocity (m/s) x"""

    @abstractmethod
    def velocity_longitudinal(self, index: int | None = None) -> float:
        """Longitudinal velocity (m/s) y"""

    @abstractmethod
    def velocity_vertical(self, index: int | None = None) -> float:
        """Vertical velocity (m/s) z"""

    @abstractmethod
    def speed(self, index: int | None = None) -> float:
        """Speed (m/s)"""

    @abstractmethod
    def downforce_front(self, index: int | None = None) -> float:
        """Downforce front (Newtons)"""

    @abstractmethod
    def downforce_rear(self, index: int | None = None) -> float:
        """Downforce rear (Newtons)"""

    @abstractmethod
    def damage_severity(self, index: int | None = None) -> tuple[int, int, int, int, int, int, int, int]:
        """Damage severity, sort row by row from left to right, top to bottom"""

    @abstractmethod
    def aero_damage(self, index: int | None = None) -> float:
        """Aerodynamic damage (fraction), 0.0 no damage, 1.0 totaled"""

    @abstractmethod
    def integrity(self, index: int | None = None) -> float:
        """Vehicle integrity"""

    @abstractmethod
    def is_detached(self, index: int | None = None) -> bool:
        """Whether any vehicle parts are detached"""

    @abstractmethod
    def impact_time(self, index: int | None = None) -> float:
        """Last impact time stamp (seconds)"""

    @abstractmethod
    def impact_magnitude(self, index: int | None = None) -> float:
        """Last impact magnitude"""

    @abstractmethod
    def impact_position(self, index: int | None = None) -> tuple[float, float]:
        """Last impact position x,y coordinates"""


class Wheel(ABC):
    """Wheel & suspension"""

    __slots__ = ()

    @abstractmethod
    def camber(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel camber (radians)"""

    @abstractmethod
    def toe(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel toe (radians)"""

    @abstractmethod
    def toe_symmetric(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel toe symmetric (radians)"""

    @abstractmethod
    def rotation(self, index: int | None = None) -> tuple[float, ...]:
        """Wheel rotation (radians per second)"""

    @abstractmethod
    def velocity_lateral(self, index: int | None = None) -> tuple[float, ...]:
        """Lateral velocity (m/s) x"""

    @abstractmethod
    def velocity_longitudinal(self, index: int | None = None) -> tuple[float, ...]:
        """Longitudinal velocity (m/s) y"""

    @abstractmethod
    def slip_angle_fl(self, index: int | None = None) -> float:
        """Slip angle (radians) front left"""

    @abstractmethod
    def slip_angle_fr(self, index: int | None = None) -> float:
        """Slip angle (radians) front right"""

    @abstractmethod
    def slip_angle_rl(self, index: int | None = None) -> float:
        """Slip angle (radians) rear left"""

    @abstractmethod
    def slip_angle_rr(self, index: int | None = None) -> float:
        """Slip angle (radians) rear right"""

    @abstractmethod
    def ride_height(self, index: int | None = None) -> tuple[float, ...]:
        """Ride height (convert meters to millimeters)"""

    @abstractmethod
    def third_spring_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Third spring deflection front & rear (convert meters to millimeters)"""

    @abstractmethod
    def suspension_deflection(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension deflection (convert meters to millimeters)"""

    @abstractmethod
    def suspension_force(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension force (Newtons)"""

    @abstractmethod
    def suspension_damage(self, index: int | None = None) -> tuple[float, ...]:
        """Suspension damage (fraction), 0.0 no damage, 1.0 totaled"""

    @abstractmethod
    def position_vertical(self, index: int | None = None) -> tuple[float, ...]:
        """Vertical wheel position (convert meters to millimeters) related to vehicle"""

    @abstractmethod
    def is_detached(self, index: int | None = None) -> tuple[bool, ...]:
        """Whether wheel is detached"""

    @abstractmethod
    def offroad(self, index: int | None = None) -> int:
        """Number of wheels currently off the road"""
