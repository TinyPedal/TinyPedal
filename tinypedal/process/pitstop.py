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
Pit stop function
"""

from __future__ import annotations

from ..const_common import EMPTY_DICT, PITEST_DEFAULT
from ..regex_pattern import rex_number_extract


# Set state & counter
def set_stopgo_state(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set stop-go penalty state"""
    if raw.get("currentSetting", 0) != 0:
        if ref_time.get("SimultaneousStopGo", False):
            temp.state_stopgo = 2  # service & stopgo
        else:
            temp.state_stopgo = 1  # stopgo only
    return None


def count_tyre_change(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Count number of tyres for replacement"""
    temp.tyre_change += (raw.get("currentSetting", 0) != raw.get("default", 0))
    return None


def count_pressure_change(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Count number of tyres for pressure adjustment"""
    temp.pressure_change += (raw.get("currentSetting", 0) != raw.get("default", 0))
    return None


# Set pit time in order:
# service time (seconds), random delay (seconds), whether concurrent (0=no, 1=yes)
def set_time_damage(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - damage fix"""
    current = raw.get("currentSetting", 0)
    delay = ref_time.get("FixRandomDelay", 0)
    concurrent = ref_time.get("FixTimeConcurrent", 0)
    if current == 1:
        seconds = ref_time.get("FixAeroDamage", 0)
    elif current == 2:
        seconds = ref_time.get("FixAllDamage", 0)
    else:
        delay = seconds = 0.0
    return seconds, delay, concurrent


def set_time_driver(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - driver swap"""
    current = raw.get("currentSetting", 0)
    default = raw.get("default", 0)
    delay = ref_time.get("DriverRandom", 0)
    concurrent = ref_time.get("DriverConcurrent", 0)
    if current != default:
        seconds = ref_time.get("DriverChange", 0)
    else:
        delay = seconds = 0.0
    return seconds, delay, concurrent


def set_time_virtual_energy(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - virtual energy (percentage)"""
    current = raw.get("currentSetting", 0)
    delay = ref_time.get("virtualEnergyRandomDelay", 0)
    concurrent = ref_time.get("virtualEnergyTimeConcurrent", 0)
    seconds = ref_time.get("virtualEnergyInsert", 0)
    seconds += ref_time.get("virtualEnergyRemove", 0)
    fill_rate = ref_time.get("virtualEnergyFillRate", 0) * 100
    refill = current - temp.nrg_remaining
    if refill > 0 < fill_rate:
        seconds += refill / fill_rate
    else:
        delay = seconds = 0.0
    temp.nrg_abs_refill = current
    temp.nrg_rel_refill = refill
    return seconds, delay, concurrent


def set_time_tyre(ref_time: dict, temp: EstimatePitTime):
    """Set time - tyre change (with pressure adjustment)"""
    delay = ref_time.get("RandomTireDelay", 0)
    concurrent = ref_time.get("TireTimeConcurrent", 0)
    pressure_on_fly = ref_time.get("OnTheFlyPressure", False)
    # Whether allow to adjust pressure without change tyre
    if temp.pressure_change and (temp.tyre_change or pressure_on_fly):
        pres_seconds = ref_time.get("PressureChange", 0)
    else:
        pres_seconds = 0.0
    if 2 < temp.tyre_change:
        seconds = ref_time.get("FourTireChange", 0)
    elif 0 < temp.tyre_change:
        seconds = ref_time.get("TwoTireChange", 0)
    else:
        delay = seconds = 0.0
    return max(seconds, pres_seconds), delay, concurrent


def set_time_front_wing(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - front wing adjust"""
    current = raw.get("currentSetting", 0)
    default = raw.get("default", 0)
    if current != default:
        seconds = ref_time.get("FrontWingAdjust", 0)
    else:
        seconds = 0.0
    return seconds, 0.0, 1


def set_time_rear_wing(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - rear wing adjust"""
    current = raw.get("currentSetting", 0)
    default = raw.get("default", 0)
    if current != default:
        seconds = ref_time.get("RearWingAdjust", 0)
    else:
        seconds = 0.0
    return seconds, 0.0, 1


def set_time_radiator(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - radiator adjust"""
    current = raw.get("currentSetting", 0)
    default = raw.get("default", 0)
    if current != default:
        seconds = ref_time.get("RadiatorChange", 0)
    else:
        seconds = 0.0
    return seconds, 0.0, 1


def set_time_brake(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - brake change"""
    current = raw.get("currentSetting", 0)
    delay = ref_time.get("RandomBrakeDelay", 0)
    concurrent = ref_time.get("BrakeTimeConcurrent", 0)
    if current > 0:
        seconds = ref_time.get("BrakeChange", 0)
    else:
        delay = seconds = 0.0
    return seconds, delay, concurrent


def set_time_fuel(fuel_absolute: float, ref_time: dict, temp: EstimatePitTime):
    """Set time - fuel (liter) only"""
    delay = ref_time.get("FuelRandomDelay", 0)
    concurrent = ref_time.get("FuelTimeConcurrent", 0)
    seconds = ref_time.get("FuelInsert", 0)
    seconds += ref_time.get("FuelRemove", 0)
    fill_rate = ref_time.get("FuelFillRate", 0)
    refill = fuel_absolute - temp.fuel_remaining
    if refill > 0 < fill_rate:
        seconds += refill / fill_rate
    else:
        delay = seconds = 0.0
    temp.fuel_abs_refill = fuel_absolute
    temp.fuel_rel_refill = refill
    return seconds, delay, concurrent


def set_time_fuel_only(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - fuel (liter) only"""
    # Get absolute refuel (liter) from data string
    try:
        current = raw.get("currentSetting", 0)
        selector = raw.get("settings")
        raw_value = selector[current]["text"]
        fuel = float(rex_number_extract.search(raw_value).group())
        if "gal" in raw_value.lower():  # convert to liter
            fuel *= 3.7854118
    except (AttributeError, TypeError, IndexError, ValueError):
        fuel = 0.0
    return set_time_fuel(fuel, ref_time, temp)


def set_time_fuel_energy(raw: dict, ref_time: dict, temp: EstimatePitTime):
    """Set time - fuel (liter) relative to virtual energy"""
    # Get fuel ratio & calculate fuel
    try:
        current = raw.get("currentSetting", 0)
        selector = raw.get("settings")
        raw_value = selector[current]["text"].strip(" ")
        fuel = float(raw_value) * temp.nrg_abs_refill
    except (AttributeError, TypeError, IndexError, ValueError):
        fuel = 0.0
    return set_time_fuel(fuel, ref_time, temp)


# Pit time function map
# key = pit option name, value = pit time function
PIT_FUNC_MAP = {
    "STOP/GO:": set_stopgo_state,
    "DAMAGE:": set_time_damage,
    "DRIVER:": set_time_driver,
    "VIRTUAL ENERGY:": set_time_virtual_energy,
    "FUEL RATIO:": set_time_fuel_energy,
    "FUEL:": set_time_fuel_only,
    "FL TIRE:": count_tyre_change,
    "FR TIRE:": count_tyre_change,
    "RL TIRE:": count_tyre_change,
    "RR TIRE:": count_tyre_change,
    "FL PRESS:": count_pressure_change,
    "FR PRESS:": count_pressure_change,
    "RL PRESS:": count_pressure_change,
    "RR PRESS:": count_pressure_change,
    "F WING:": set_time_front_wing,
    "R WING:": set_time_rear_wing,
    "GRILLE:": set_time_radiator,
    "REPLACE BRAKES:": set_time_brake,
}


class EstimatePitTime():
    """Estimate total pit time"""

    __slots__ = (
        "state_stopgo",
        "tyre_change",
        "pressure_change",
        "nrg_rel_refill",
        "fuel_rel_refill",
        "nrg_abs_refill",
        "fuel_abs_refill",
        "nrg_remaining",
        "fuel_remaining",
    )

    def __init__(self):
        self.state_stopgo = 0  # 0 = no stopgo, 1 = stopgo only, 2 = service & stopgo
        self.tyre_change = 0
        self.pressure_change = 0
        self.nrg_rel_refill = 0.0
        self.fuel_rel_refill = 0.0
        self.nrg_abs_refill = 0.0
        self.fuel_abs_refill = 0.0
        self.nrg_remaining = 0.0
        self.fuel_remaining = 0.0

    def __call__(self, dataset: dict) -> tuple[float, float, float, float, int]:
        """Calculate pit stop time (handle error in upper-level function)"""
        # Get data
        pit_menu = dataset.get("pitMenu", EMPTY_DICT).get("pitMenu", None)
        ref_time = dataset.get("pitStopTimes", EMPTY_DICT).get("times", None)
        fuel_info = dataset.get("fuelInfo", EMPTY_DICT)
        # stopgo_time = dataset.get("pitStopLength", EMPTY_DICT).get("timeInSeconds", 10.0)
        if not isinstance(pit_menu, list) or not isinstance(ref_time, dict):
            return PITEST_DEFAULT
        # Update temp pit data
        self.state_stopgo = 0
        self.tyre_change = 0
        self.pressure_change = 0
        nrg_current = fuel_info.get("currentVirtualEnergy", 0.0)
        nrg_max = fuel_info.get("maxVirtualEnergy", 0.0)
        self.nrg_remaining = nrg_current / nrg_max * 100 if nrg_max else 0.0
        self.fuel_remaining = fuel_info.get("currentFuel", 0.0)
        # Setup parser
        gen_pit_time = self.__process(pit_menu, ref_time)
        # Parse data & calculate pit time
        sum_concurrent = 0.0
        sum_separate = 0.0
        sum_concurrent_delay = 0.0
        sum_separate_delay = 0.0
        for service_time, random_delay, is_concurrent in gen_pit_time:
            service_time_delay = service_time + random_delay
            # Set longest concurrent service time
            if is_concurrent:
                if sum_concurrent < service_time:
                    sum_concurrent = service_time
                if sum_concurrent_delay < service_time_delay:
                    sum_concurrent_delay = service_time_delay
            # Add up non-concurrent service time
            else:
                sum_separate += service_time
                sum_separate_delay += service_time_delay
        # Sum pit time
        return (
            sum_concurrent + sum_separate,
            sum_concurrent_delay + sum_separate_delay,
            self.fuel_rel_refill,
            self.nrg_rel_refill,
            self.state_stopgo,
        )

    def __process(self, pit_menu: list, ref_time: dict):
        """Process pit time data"""
        for raw in pit_menu:
            pit_func = PIT_FUNC_MAP.get(raw.get("name"))
            if pit_func:
                value = pit_func(raw, ref_time, self)
                if value is not None:  # output pit time data
                    yield value
                elif self.state_stopgo == 1:  # stopgo only
                    return
        yield set_time_tyre(ref_time, self)
