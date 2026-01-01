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
Track info preset function
"""

from __future__ import annotations

from ..const_file import ConfigType
from ..setting import cfg
from ..template.setting_tracks import TRACKINFO_DEFAULT
from ..validator import invalid_save_name


def add_missing_track(track_name: str) -> dict:
    """Add missing track info to tracks preset"""
    new_data = TRACKINFO_DEFAULT.copy()
    cfg.user.tracks[track_name] = new_data
    return new_data


def load_track_info(track_name: str) -> dict:
    """Load track info from tracks preset"""
    return cfg.user.tracks.get(track_name, TRACKINFO_DEFAULT)


def save_track_info(track_name: str, **track_info: dict) -> None:
    """Save track info to tracks preset"""
    if invalid_save_name(track_name):
        return
    track = cfg.user.tracks.get(track_name)
    if not isinstance(track, dict):
        track = add_missing_track(track_name)
    track.update(track_info)
    cfg.save(cfg_type=ConfigType.TRACKS)
