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
Init logger, state, signal
"""

import logging

from PySide2.QtCore import QObject, Signal

# Create logger
logger = logging.getLogger(__package__)


class RealtimeState:
    """Realtime state

    Check realtime data update state without calling methods.
    Change state via OverlayControl.

    Attributes:
        active: whether is active (driving or overriding) state.
        paused: whether data stopped updating.
    """

    __slots__ = (
        "active",
        "paused",
    )

    def __init__(self):
        self.active: bool = False
        self.paused: bool = True


class OverlaySignal(QObject):
    """Overlay signal

    Attributes:
        hidden: signal for toggling auto hide state.
        locked: signal for toggling lock state.
        reload: signal for reloading preset, should only be emitted after app fully loaded.
        paused: signal for pausing and resuming overlay timer.
        iconify: signal for toggling taskbar icon visibility state (for VR compatibility).
        updates: signal for checking version updates.
    """

    hidden = Signal(bool)
    locked = Signal(bool)
    reload = Signal(bool)
    paused = Signal(bool)
    iconify = Signal(bool)
    updates = Signal(bool)
    __slots__ = ()


realtime_state = RealtimeState()
overlay_signal = OverlaySignal()
