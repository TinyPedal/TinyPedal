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
Units conversion function, selector, symbol
"""

from __future__ import annotations

from typing import Callable


def pass_value(v: float) -> float:
    """Pass value"""
    return v


# Unit conversion
def meter_to_millimeter(meter: float) -> float:
    """Meter to Millimeter"""
    return meter * 1000


def meter_to_feet(meter: float) -> float:
    """Meter to Feet"""
    return meter * 3.2808399


def meter_to_kilometer(meter: float) -> float:
    """Meter to Kilometer"""
    return meter * 0.001


def meter_to_mile(meter: float) -> float:
    """Meter to Mile"""
    return meter / 1609.344


def mps_to_kph(meter: float) -> float:
    """Meter per sec to Kilometers per hour"""
    return meter * 3.6


def mps_to_mph(meter: float) -> float:
    """Meter per sec to Miles per hour"""
    return meter * 2.23693629


def celsius_to_fahrenheit(temperature: float) -> float:
    """Celsius to Fahrenheit"""
    return temperature * 1.8 + 32


def liter_to_gallon(liter: float) -> float:
    """Liter to Gallon"""
    return liter * 0.26417205


def kelvin_to_celsius(kelvin: float) -> float:
    """Kelvin to Celsius"""
    return kelvin - 273.15


def kpa_to_psi(kilopascal: float) -> float:
    """Kilopascal to Pounds per square inch (psi)"""
    return kilopascal * 0.14503774


def kpa_to_bar(kilopascal: float) -> float:
    """Kilopascal to bar"""
    return kilopascal * 0.01


def kw_to_hp(kilowatt: float) -> float:
    """Kilowatt to Imperial Horsepower (hp)"""
    return kilowatt * 1.341


def kw_to_ps(kilowatt: float) -> float:
    """Kilowatt to Metric Horsepower (ps)"""
    return kilowatt * 1.3596


# Set unit conversion function
def set_unit_distance(unit_name: str = "Meter") -> Callable:
    """Set unit distance"""
    if unit_name == "Feet":
        return meter_to_feet
    if unit_name == "Kilometer":
        return meter_to_kilometer
    if unit_name == "Mile":
        return meter_to_mile
    return pass_value


def set_unit_fuel(unit_name: str = "Liter") -> Callable:
    """Set unit fuel"""
    if unit_name == "Gallon":
        return liter_to_gallon
    return pass_value


def set_unit_power(unit_name: str = "Kilowatt") -> Callable:
    """Set unit power"""
    if unit_name == "Horsepower":
        return kw_to_hp
    if unit_name == "Metric Horsepower":
        return kw_to_ps
    return pass_value


def set_unit_pressure(unit_name: str = "kPa") -> Callable:
    """Set unit pressure"""
    if unit_name == "psi":
        return kpa_to_psi
    if unit_name == "bar":
        return kpa_to_bar
    return pass_value


def set_unit_speed(unit_name: str = "m/s") -> Callable:
    """Set unit speed"""
    if unit_name == "KPH":
        return mps_to_kph
    if unit_name == "MPH":
        return mps_to_mph
    return pass_value


def set_unit_temperature(unit_name: str = "Celsius") -> Callable:
    """Set unit temperature"""
    if unit_name == "Fahrenheit":
        return celsius_to_fahrenheit
    return pass_value


# Set unit symbol string
def set_symbol_distance(unit_name: str = "Meter") -> str:
    """Set symbol distance"""
    if unit_name == "Feet":
        return "ft"
    if unit_name == "Kilometer":
        return "km"
    if unit_name == "Mile":
        return "mi"
    return "m"


def set_symbol_fuel(unit_name: str = "Liter") -> str:
    """Set symbol fuel"""
    if unit_name == "Gallon":
        return "gal"
    return "L"


def set_symbol_power(unit_name: str = "Kilowatt") -> str:
    """Set symbol power"""
    if unit_name == "Horsepower":
        return "hp"
    if unit_name == "Metric Horsepower":
        return "ps"
    return "kW"


def set_symbol_pressure(unit_name: str = "kPa") -> str:
    """Set symbol pressure"""
    if unit_name == "psi":
        return "psi"
    if unit_name == "bar":
        return "bar"
    return "kPa"


def set_symbol_speed(unit_name: str = "m/s") -> str:
    """Set symbol speed"""
    if unit_name == "KPH":
        return "km/h"
    if unit_name == "MPH":
        return "mph"
    return "m/s"


def set_symbol_temperature(unit_name: str = "Celsius") -> str:
    """Set symbol temperature"""
    if unit_name == "Fahrenheit":
        return "°F"
    return "°C"
