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
Hotkey command function
"""

from __future__ import annotations

from .. import app_signal, loader, overlay_signal, realtime_state
from ..api_control import API_PACK, api
from ..const_file import ConfigType, FileExt
from ..setting import cfg


def hotkey_overlay_visibility():
    """Command - overlay visibility"""
    realtime_state.hidden = not realtime_state.hidden
    overlay_signal.hidden.emit(realtime_state.hidden)


def hotkey_overlay_lock():
    """Command - overlay lock"""
    cfg.overlay["fixed_position"] = not cfg.overlay["fixed_position"]
    cfg.save()
    overlay_signal.locked.emit(cfg.overlay["fixed_position"])


def hotkey_vr_compatibility():
    """Command - vr compatibility"""
    cfg.overlay["vr_compatibility"] = not cfg.overlay["vr_compatibility"]
    cfg.save()
    overlay_signal.iconify.emit(cfg.overlay["vr_compatibility"])


def hotkey_restart_api():
    """Command - restart api"""
    api.restart()
    app_signal.refresh.emit(True)


def hotkey_select_next_api():
    """Command - select next api"""
    api_name = api.name
    api_list = tuple(_api.NAME for _api in API_PACK)
    next_index = 0
    if api_name in api_list:
        next_index = api_list.index(api_name) + 1
        if next_index >= len(api_list):
            next_index = 0
    cfg.api_name = api_list[next_index]
    if cfg.telemetry["enable_api_selection_from_preset"]:
        save_type = ConfigType.SETTING
    else:
        save_type = ConfigType.CONFIG
    cfg.save(cfg_type=save_type)
    api.restart()
    app_signal.refresh.emit(True)


def hotkey_select_previous_api():
    """Command - select previous api"""
    api_name = api.name
    api_list = tuple(_api.NAME for _api in API_PACK)
    next_index = 0
    if api_name in api_list:
        next_index = api_list.index(api_name) - 1
        if next_index < 0:
            next_index = max(len(api_list) - 1, 0)
    cfg.api_name = api_list[next_index]
    if cfg.telemetry["enable_api_selection_from_preset"]:
        save_type = ConfigType.SETTING
    else:
        save_type = ConfigType.CONFIG
    cfg.save(cfg_type=save_type)
    api.restart()
    app_signal.refresh.emit(True)


def hotkey_reload_preset():
    """Command - reload preset"""
    app_signal.reload.emit(True)


def hotkey_load_next_preset():
    """Command - load next preset (in ascending order)"""
    preset_list = cfg.preset_files(by_date=False, reverse=False)
    loaded_preset = cfg.filename.setting[:-5]
    next_index = 0
    if loaded_preset in preset_list:
        next_index = preset_list.index(loaded_preset) + 1
        if next_index >= len(preset_list):
            next_index = 0
    cfg.set_next_to_load(f"{preset_list[next_index]}{FileExt.JSON}")
    app_signal.reload.emit(True)


def hotkey_load_previous_preset():
    """Command - load previous preset (in ascending order)"""
    preset_list = cfg.preset_files(by_date=False, reverse=False)
    loaded_preset = cfg.filename.setting[:-5]
    next_index = 0
    if loaded_preset in preset_list:
        next_index = preset_list.index(loaded_preset) - 1
        if next_index < 0:
            next_index = max(len(preset_list) - 1, 0)
    cfg.set_next_to_load(f"{preset_list[next_index]}{FileExt.JSON}")
    app_signal.reload.emit(True)


def hotkey_spectate_mode():
    """Command - spectate mode"""
    cfg.api["enable_player_index_override"] = not cfg.api["enable_player_index_override"]
    cfg.save()
    app_signal.refresh.emit(True)


def hotkey_spectate_next_driver():
    """Command - spectate next driver (overall position)"""
    if not cfg.api["enable_player_index_override"]:
        return
    place = api.read.vehicle.place() + 1
    total_vehicles = api.read.vehicle.total_vehicles()
    if place > total_vehicles:
        place = 0
    for player_index in range(total_vehicles):
        if api.read.vehicle.place(player_index) == place:
            cfg.api["player_index"] = player_index
            api.setup()
            cfg.save()
            return


def hotkey_spectate_previous_driver():
    """Command - spectate previous driver (overall position)"""
    if not cfg.api["enable_player_index_override"]:
        return
    place = api.read.vehicle.place() - 1
    total_vehicles = api.read.vehicle.total_vehicles()
    if place < 1:
        place = total_vehicles
    for player_index in range(total_vehicles):
        if api.read.vehicle.place(player_index) == place:
            cfg.api["player_index"] = player_index
            api.setup()
            cfg.save()
            return


def hotkey_pace_notes_playback():
    """Command - pace notes playback"""
    cfg.user.setting["pace_notes_playback"]["enable"] = not cfg.user.setting["pace_notes_playback"]["enable"]
    cfg.save()
    app_signal.refresh.emit(True)


def hotkey_restart_application():
    """Command - restart application"""
    loader.restart()


def hotkey_quit_application():
    """Command - quit application"""
    app_signal.quitapp.emit(True)


COMMANDS_HOTKEY = (
    ("overlay_visibility", hotkey_overlay_visibility),
    ("overlay_lock", hotkey_overlay_lock),
    ("vr_compatibility", hotkey_vr_compatibility),
    ("restart_api", hotkey_restart_api),
    ("select_next_api", hotkey_select_next_api),
    ("select_previous_api", hotkey_select_previous_api),
    ("reload_preset", hotkey_reload_preset),
    ("load_next_preset", hotkey_load_next_preset),
    ("load_previous_preset", hotkey_load_previous_preset),
    ("spectate_mode", hotkey_spectate_mode),
    ("spectate_next_driver", hotkey_spectate_next_driver),
    ("spectate_previous_driver", hotkey_spectate_previous_driver),
    ("pace_notes_playback", hotkey_pace_notes_playback),
    ("restart_application", hotkey_restart_application),
    ("quit_application", hotkey_quit_application),
)
