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
Decorator
"""

from functools import wraps
from typing import Callable


# Function
def dwrap(gen: Callable):
    """Wrapper for default (mutable) data generator"""
    return gen


# Function decorator
def generator_init(func):
    """Initialize generator for send() method, returns None if StopIteration"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        generator = func(*args, **kwargs)
        try:
            next(generator)
        except StopIteration:
            generator = None
        return generator

    return wrapper


# Class decorator
def _init_slot_data(self, defaults: dict):
    """Init slot data"""
    for key, value in defaults.items():
        if callable(value):
            setattr(self, key, value())
        else:
            setattr(self, key, value)


def slotclass(cls):
    """Generate __slots__ from __annotations__ for custom data class"""

    def wrap(cls):
        if "__annotations__" not in cls.__dict__:
            raise TypeError("missing __annotations__")

        cls_attrs = dict(cls.__dict__)
        # Add slots from __annotations__
        data_keys = cls_attrs["__annotations__"].keys()
        cls_attrs["__slots__"] = data_keys
        # Store default key, value, remove class vars
        defaults = {key: cls_attrs.pop(key) for key in data_keys}
        # Remove __dict__
        cls_attrs.pop("__dict__")
        # Set __init__
        cls_attrs["__init__"] = lambda self: _init_slot_data(self, defaults)
        # Create new class
        cls = type(cls)(cls.__name__, cls.__bases__, cls_attrs)
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


def constantclass(cls):
    """Create immutable read-only constant class"""

    def wrap(cls):
        if "__annotations__" not in cls.__dict__:
            raise TypeError("missing __annotations__")

        cls_attrs = dict(cls.__dict__)
        # Add empty slots
        cls_attrs["__slots__"] = ()
        # Remove __dict__
        cls_attrs.pop("__dict__")
        # Create new class
        cls = type(cls)(cls.__name__, cls.__bases__, cls_attrs)
        # Instantiate & freeze class variables
        return cls()

    if cls is None:
        return wrap
    return wrap(cls)
