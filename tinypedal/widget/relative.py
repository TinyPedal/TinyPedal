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
Relative Widget
"""

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import MAX_SECONDS, TEXT_NOLAPTIME, TEXT_PLACEHOLDER
from ..formatter import random_color_class, shorten_driver_name
from ..module_info import minfo
from ..userfile.brand_logo import load_brand_logo_file
from ..userfile.heatmap import select_compound_symbol
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap_vert=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.drv_width = max(int(self.wcfg["driver_name_width"]), 1)
        self.veh_width = max(int(self.wcfg["vehicle_name_width"]), 1)
        self.brd_width = max(int(self.wcfg["brand_logo_width"]), 1)
        self.brd_height = max(self.wcfg["font_size"], 1)
        self.cls_width = max(int(self.wcfg["class_width"]), 0)
        self.gap_width = max(int(self.wcfg["time_gap_width"]), 1)
        self.gap_decimals = max(int(self.wcfg["time_gap_decimal_places"]), 0)
        self.nrg_decimals = max(int(self.wcfg["energy_remaining_decimal_places"]), 0)
        self.nrg_width = 3 + self.nrg_decimals + (self.nrg_decimals > 0)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Max display players
        veh_add_front = min(max(int(self.wcfg["additional_players_front"]), 0), 60)
        veh_add_behind = min(max(int(self.wcfg["additional_players_behind"]), 0), 60)
        self.veh_range = max(7 + veh_add_front + veh_add_behind, 7)

        # Empty dataset
        self.pixmap_brandlogo = {}
        self.row_visible = [False] * self.veh_range

        # Driver position
        if self.wcfg["show_position"]:
            self.bar_style_pos = self.set_qss_lap_difference(
                fg_color=self.wcfg["font_color_position"],
                bg_color=self.wcfg["bkg_color_position"],
                plr_fg_color=self.wcfg["font_color_player_position"],
                plr_bg_color=self.wcfg["bkg_color_player_position"],
            )
            self.bars_pos = self.set_qlabel(
                style=self.bar_style_pos[0],
                width=2 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_pos,
                column_index=self.wcfg["column_index_position"],
            )
        # Driver position change
        if self.wcfg["show_position_change"]:
            self.bar_style_pgl = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_position_same"],
                    bg_color=self.wcfg["bkg_color_position_same"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_position_gain"],
                    bg_color=self.wcfg["bkg_color_position_gain"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_position_loss"],
                    bg_color=self.wcfg["bkg_color_position_loss"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_position_change"],
                    bg_color=self.wcfg["bkg_color_player_position_change"])
            )
            self.bars_pgl = self.set_qlabel(
                style=self.bar_style_pgl[0],
                width=3 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_pgl,
                column_index=self.wcfg["column_index_position_change"],
            )
        # Driver name
        if self.wcfg["show_driver_name"]:
            self.bar_style_drv = self.set_qss_lap_difference(
                fg_color=self.wcfg["font_color_driver_name"],
                bg_color=self.wcfg["bkg_color_driver_name"],
                plr_fg_color=self.wcfg["font_color_player_driver_name"],
                plr_bg_color=self.wcfg["bkg_color_player_driver_name"],
            )
            self.bars_drv = self.set_qlabel(
                style=self.bar_style_drv[0],
                width=self.drv_width * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_drv,
                column_index=self.wcfg["column_index_driver"],
            )
        # Vehicle name
        if self.wcfg["show_vehicle_name"]:
            self.bar_style_veh = self.set_qss_lap_difference(
                fg_color=self.wcfg["font_color_vehicle_name"],
                bg_color=self.wcfg["bkg_color_vehicle_name"],
                plr_fg_color=self.wcfg["font_color_player_vehicle_name"],
                plr_bg_color=self.wcfg["bkg_color_player_vehicle_name"],
            )
            self.bars_veh = self.set_qlabel(
                style=self.bar_style_veh[0],
                width=self.veh_width * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_veh,
                column_index=self.wcfg["column_index_vehicle"],
            )
        # Brand logo
        if self.wcfg["show_brand_logo"]:
            self.bar_style_brd = (
                self.set_qss(
                    bg_color=self.wcfg["bkg_color_brand_logo"]),
                self.set_qss(
                    bg_color=self.wcfg["bkg_color_player_brand_logo"])
            )
            self.bars_brd = self.set_qlabel(
                style=self.bar_style_brd[0],
                width=self.brd_width,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_brd,
                column_index=self.wcfg["column_index_brand_logo"],
            )
        # Time gap
        if self.wcfg["show_time_gap"]:
            self.bar_style_gap = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_time_gap"],
                    bg_color=self.wcfg["bkg_color_time_gap"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_time_gap"],
                    bg_color=self.wcfg["bkg_color_player_time_gap"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_nearest_time_gap"],
                    bg_color=self.wcfg["bkg_color_nearest_time_gap"])
            )
            self.nearest_time_gap = (
                -max(self.wcfg["nearest_time_gap_threshold_behind"], 0),
                max(self.wcfg["nearest_time_gap_threshold_front"], 0),
            )
            self.bars_gap = self.set_qlabel(
                style=self.bar_style_gap[0],
                width=self.gap_width * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_gap,
                column_index=self.wcfg["column_index_timegap"],
            )
        # Vehicle laptime
        if self.wcfg["show_laptime"]:
            self.bar_style_lpt = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_laptime"],
                    bg_color=self.wcfg["bkg_color_laptime"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_laptime"],
                    bg_color=self.wcfg["bkg_color_player_laptime"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_fastest_last_laptime"],
                    bg_color=self.wcfg["bkg_color_fastest_last_laptime"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_fastest_last_laptime"],
                    bg_color=self.wcfg["bkg_color_player_fastest_last_laptime"])
            )
            self.bars_lpt = self.set_qlabel(
                style=self.bar_style_lpt[0],
                width=8 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_lpt,
                column_index=self.wcfg["column_index_laptime"],
            )
        # Vehicle best laptime
        if self.wcfg["show_best_laptime"]:
            self.bar_style_blp = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_best_laptime"],
                    bg_color=self.wcfg["bkg_color_best_laptime"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_best_laptime"],
                    bg_color=self.wcfg["bkg_color_player_best_laptime"])
            )
            self.bars_blp = self.set_qlabel(
                style=self.bar_style_blp[0],
                width=8 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_blp,
                column_index=self.wcfg["column_index_best_laptime"],
            )
        # Position in class
        if self.wcfg["show_position_in_class"]:
            self.bar_style_pic = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_position_in_class"],
                    bg_color=self.wcfg["bkg_color_position_in_class"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_position_in_class"],
                    bg_color=self.wcfg["bkg_color_player_position_in_class"])
            )
            self.bars_pic = self.set_qlabel(
                style=self.bar_style_pic[0],
                width=2 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_pic,
                column_index=self.wcfg["column_index_position_in_class"],
            )
        # Vehicle class
        if self.wcfg["show_class"]:
            bar_style_cls = self.set_qss(
                fg_color=self.wcfg["font_color_class"],
                bg_color=self.wcfg["bkg_color_class"]
            )
            self.bars_cls = self.set_qlabel(
                style=bar_style_cls,
                width=self.cls_width * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_cls,
                column_index=self.wcfg["column_index_class"],
            )
        # Vehicle in pit
        if self.wcfg["show_pit_status"]:
            self.pit_status_text = (
                "",
                self.wcfg["pit_status_text"],
                self.wcfg["garage_status_text"],
                self.wcfg["yellow_flag_status_text"],
            )
            self.bar_style_pit = (
                "",
                self.set_qss(
                    fg_color=self.wcfg["font_color_pit"],
                    bg_color=self.wcfg["bkg_color_pit"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_garage"],
                    bg_color=self.wcfg["bkg_color_garage"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_yellow_flag"],
                    bg_color=self.wcfg["bkg_color_yellow_flag"])
            )
            self.bars_pit = self.set_qlabel(
                style=self.bar_style_pit[0],
                width=max(map(len, self.pit_status_text)) * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_pit,
                column_index=self.wcfg["column_index_pitstatus"],
            )
        # Tyre compound index
        if self.wcfg["show_tyre_compound"]:
            self.bar_style_tcp = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_tyre_compound"],
                    bg_color=self.wcfg["bkg_color_tyre_compound"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_tyre_compound"],
                    bg_color=self.wcfg["bkg_color_player_tyre_compound"])
            )
            self.bars_tcp = self.set_qlabel(
                style=self.bar_style_tcp[0],
                width=2 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_tcp,
                column_index=self.wcfg["column_index_tyre_compound"],
            )
        # Pitstop count
        if self.wcfg["show_pitstop_count"]:
            self.bar_style_psc = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_pitstop_count"],
                    bg_color=self.wcfg["bkg_color_pitstop_count"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_pitstop_count"],
                    bg_color=self.wcfg["bkg_color_player_pitstop_count"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_pit_request"],
                    bg_color=self.wcfg["bkg_color_pit_request"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_penalty_count"],
                    bg_color=self.wcfg["bkg_color_penalty_count"])
            )
            self.bars_psc = self.set_qlabel(
                style=self.bar_style_psc[0],
                width=2 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_psc,
                column_index=self.wcfg["column_index_pitstop_count"],
            )
        # Remaining energy
        if self.wcfg["show_energy_remaining"]:
            self.bar_style_nrg = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_energy_remaining_unavailable"],
                    bg_color=self.wcfg["bkg_color_energy_remaining"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_energy_remaining_high"],
                    bg_color=self.wcfg["bkg_color_energy_remaining"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_energy_remaining_low"],
                    bg_color=self.wcfg["bkg_color_energy_remaining"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_energy_remaining_critical"],
                    bg_color=self.wcfg["bkg_color_energy_remaining"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_energy_remaining"],
                    bg_color=self.wcfg["bkg_color_player_energy_remaining"])
            )
            self.bars_nrg = self.set_qlabel(
                style=self.bar_style_nrg[0],
                width=self.nrg_width * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_nrg,
                column_index=self.wcfg["column_index_energy_remaining"],
            )
        # Vehicle integrity
        if self.wcfg["show_vehicle_integrity"]:
            self.bar_style_dmg = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_vehicle_integrity_full"],
                    bg_color=self.wcfg["bkg_color_vehicle_integrity"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_vehicle_integrity_high"],
                    bg_color=self.wcfg["bkg_color_vehicle_integrity"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_vehicle_integrity_low"],
                    bg_color=self.wcfg["bkg_color_vehicle_integrity"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_vehicle_integrity"],
                    bg_color=self.wcfg["bkg_color_player_vehicle_integrity"])
            )
            self.bars_dmg = self.set_qlabel(
                style=self.bar_style_dmg[0],
                width=1 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_dmg,
                column_index=self.wcfg["column_index_vehicle_integrity"],
            )
        # Stint laps
        if self.wcfg["show_stint_laps"]:
            self.bar_style_stl = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_stint_laps"],
                    bg_color=self.wcfg["bkg_color_stint_laps"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_stint_laps"],
                    bg_color=self.wcfg["bkg_color_player_stint_laps"])
            )
            self.bars_stl = self.set_qlabel(
                style=self.bar_style_stl[0],
                width=5 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_stl,
                column_index=self.wcfg["column_index_stint_laps"],
            )
        # Speed trap
        if self.wcfg["show_speed_trap"]:
            self.unit_speed = units.set_unit_speed(self.cfg.units["speed_unit"])
            self.bar_style_spd = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_speed_trap"],
                    bg_color=self.wcfg["bkg_color_speed_trap"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_speed_trap"],
                    bg_color=self.wcfg["bkg_color_player_speed_trap"])
            )
            self.bars_spd = self.set_qlabel(
                style=self.bar_style_spd[0],
                width=5 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_spd,
                column_index=self.wcfg["column_index_speed_trap"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        relative_list = minfo.relative.relative
        total_rel_idx = len(relative_list)
        player_idx = minfo.vehicles.playerIndex
        plr_veh_info = minfo.vehicles.dataSet[player_idx]
        in_race = api.read.session.in_race()

        # Relative update
        for idx in range(self.veh_range):

            if idx < total_rel_idx:
                rel_time_gap, rel_idx = relative_list[idx]
            else:
                rel_time_gap, rel_idx = 0.0, -2

            # Set row state: 1 - show text, 0 - hide text
            if rel_idx >= 0:
                self.row_visible[idx] = True
                state = 1
            elif not self.row_visible[idx]:
                continue  # skip if already empty
            else:
                self.row_visible[idx] = False
                state = 0

            # Get vehicle dataset
            veh_info = minfo.vehicles.dataSet[rel_idx]
            # Highlighted player
            hi_player = self.wcfg["show_player_highlighted"] and veh_info.isPlayer
            # Check whether is lapped
            is_lapped = veh_info.isLapped
            # Driver position
            if self.wcfg["show_position"]:
                self.update_pos(self.bars_pos[idx], veh_info.positionOverall, is_lapped, hi_player, state)
            # Driver position change
            if self.wcfg["show_position_change"]:
                if self.wcfg["show_position_change_in_class"]:
                    pos_diff = veh_info.qualifyInClass - veh_info.positionInClass
                else:
                    pos_diff = veh_info.qualifyOverall - veh_info.positionOverall
                self.update_pgl(self.bars_pgl[idx], pos_diff, hi_player, state)
            # Driver name
            if self.wcfg["show_driver_name"]:
                self.update_drv(self.bars_drv[idx], veh_info.driverName, is_lapped, hi_player, state)
            # Vehicle name
            if self.wcfg["show_vehicle_name"]:
                self.update_veh(self.bars_veh[idx], veh_info.vehicleName, is_lapped, hi_player, state)
            # Brand logo
            if self.wcfg["show_brand_logo"]:
                self.update_brd(self.bars_brd[idx], veh_info.vehicleName, hi_player, state)
            # Time gap
            if self.wcfg["show_time_gap"]:
                self.update_gap(self.bars_gap[idx], rel_time_gap, hi_player, state)
            # Vehicle laptime
            if self.wcfg["show_laptime"]:
                if self.wcfg["show_pitstop_duration_while_requested_pitstop"] and plr_veh_info.pitRequested:
                    laptime = self.set_pittime(veh_info.inPit, veh_info.pitTimer.elapsed)
                    is_class_best = False
                elif veh_info.pitTimer.pitting:
                    laptime = self.set_pittime(veh_info.inPit, veh_info.pitTimer.elapsed)
                    is_class_best = False
                else:
                    laptime = self.set_laptime(veh_info.lastLapTime, veh_info.isValidLap)
                    is_class_best = veh_info.isClassFastestLastLap
                self.update_lpt(self.bars_lpt[idx], laptime, is_class_best, hi_player, state)
            # Vehicle best laptime
            if self.wcfg["show_best_laptime"]:
                if in_race and self.wcfg["show_best_laptime_from_recent_laps_in_race"]:
                    laptime = veh_info.lapTimeHistory.best()
                else:
                    laptime = veh_info.bestLapTime
                self.update_blp(self.bars_blp[idx], laptime, hi_player, state)
            # Position in class
            if self.wcfg["show_position_in_class"]:
                self.update_pic(self.bars_pic[idx], veh_info.positionInClass, veh_info.vehicleClass, hi_player, state)
            # Vehicle class
            if self.wcfg["show_class"]:
                self.update_cls(self.bars_cls[idx], veh_info.vehicleClass, state)
            # Vehicle in pit
            if self.wcfg["show_pit_status"]:
                self.update_pit(self.bars_pit[idx], veh_info.inPit, veh_info.isYellow, state)
            # Tyre compound index
            if self.wcfg["show_tyre_compound"]:
                self.update_tcp(self.bars_tcp[idx], veh_info.tireCompoundFront, veh_info.tireCompoundRear, hi_player, state)
            # Pitstop count
            if self.wcfg["show_pitstop_count"]:
                self.update_psc(self.bars_psc[idx], veh_info.numPitStops, veh_info.pitRequested, hi_player, state)
            # Remaining energy
            if self.wcfg["show_energy_remaining"]:
                self.update_nrg(self.bars_nrg[idx], veh_info.energyRemaining, hi_player, state)
            # Vehicle integrity
            if self.wcfg["show_vehicle_integrity"]:
                self.update_dmg(self.bars_dmg[idx], veh_info.vehicleIntegrity, hi_player, state)
            # Stint laps
            if self.wcfg["show_stint_laps"]:
                self.update_stl(self.bars_stl[idx], veh_info.currentStintLaps, veh_info.estimatedStintLaps, hi_player, state)
            # Speed trap
            if self.wcfg["show_speed_trap"]:
                self.update_spd(self.bars_spd[idx], veh_info.speedTrap.speed, hi_player, state)

    # GUI update methods
    def update_pos(self, target, *data):
        """Driver position"""
        if target.last != data:
            target.last = data
            if data[2]:  # highlight player
                color = self.bar_style_pos[1]
            elif self.wcfg["show_lap_difference"]:
                color = self.bar_style_pos[lap_difference_index(data[1])]
            else:
                color = self.bar_style_pos[0]
            if data[-1]:
                text = f"{data[0]:02d}"
            else:
                text = ""
            target.setText(text)
            target.updateStyle(color)

    def update_pgl(self, target, *data):
        """Driver position change (gain/loss)"""
        if target.last != data:
            target.last = data
            if data[-1]:
                pos_diff = data[0]
                if pos_diff > 0:
                    text = f"▲{pos_diff: >2}"
                    color_index = 1
                elif pos_diff < 0:
                    text = f"▼{-pos_diff: >2}"
                    color_index = 2
                else:
                    text = "- 0"
                    color_index = 0
                if data[1]:
                    color_index = 3
            else:
                text = ""
                color_index = 0
            target.setText(text)
            target.updateStyle(self.bar_style_pgl[color_index])

    def update_drv(self, target, *data):
        """Driver name"""
        if target.last != data:
            target.last = data
            if data[2]:  # highlight player
                color = self.bar_style_drv[1]
            elif self.wcfg["show_lap_difference"]:
                color = self.bar_style_drv[lap_difference_index(data[1])]
            else:
                color = self.bar_style_drv[0]
            if data[-1]:
                if self.wcfg["driver_name_shorten"]:
                    text = shorten_driver_name(data[0])
                else:
                    text = data[0]
                if self.wcfg["driver_name_uppercase"]:
                    text = text.upper()
                if self.wcfg["driver_name_align_center"]:
                    text = text[:self.drv_width]
                else:
                    text = text[:self.drv_width].ljust(self.drv_width)
            else:
                text = ""
            target.setText(text)
            target.updateStyle(color)

    def update_veh(self, target, *data):
        """Vehicle name"""
        if target.last != data:
            target.last = data
            if data[2]:  # highlight player
                color = self.bar_style_veh[1]
            elif self.wcfg["show_lap_difference"]:
                color = self.bar_style_veh[lap_difference_index(data[1])]
            else:
                color = self.bar_style_veh[0]
            if data[-1]:
                if self.wcfg["show_vehicle_brand_as_name"]:
                    text = self.cfg.user.brands.get(data[0], data[0])
                else:
                    text = data[0]
                if self.wcfg["vehicle_name_uppercase"]:
                    text = text.upper()
                if self.wcfg["vehicle_name_align_center"]:
                    text = text[:self.veh_width]
                else:
                    text = text[:self.veh_width].ljust(self.veh_width)
            else:
                text = ""
            target.setText(text)
            target.updateStyle(color)

    def update_brd(self, target, *data):
        """Brand logo"""
        if target.last != data:
            target.last = data
            if data[-1]:
                brand_name = self.cfg.user.brands.get(data[0], data[0])
            else:
                brand_name = ""
            target.setPixmap(self.set_brand_logo(brand_name))
            target.updateStyle(self.bar_style_brd[data[1]])

    def update_gap(self, target, *data):
        """Time gap"""
        if target.last != data:
            target.last = data
            if data[1]:  # highlight player
                color_index = 1
            elif (self.wcfg["show_highlighted_nearest_time_gap"] and data[-1] and
                  self.nearest_time_gap[0] <= data[0] <= self.nearest_time_gap[1]):
                color_index = 2
            else:
                color_index = 0
            if data[-1]:
                if self.wcfg["show_time_gap_sign"] and data[0] != 0:
                    value = f"{-data[0]:+.{self.gap_decimals}f}"
                else:
                    value = f"{abs(data[0]):.{self.gap_decimals}f}"
                if self.wcfg["time_gap_align_center"]:
                    text = value[:self.gap_width].strip(".")
                else:
                    text = value[:self.gap_width].strip(".").rjust(self.gap_width)
            else:
                text = ""
            target.setText(text)
            target.updateStyle(self.bar_style_gap[color_index])

    def update_lpt(self, target, *data):
        """Vehicle laptime"""
        if target.last != data:
            target.last = data
            if self.wcfg["show_highlighted_fastest_last_laptime"] and data[1]:
                color_index = 2 + data[2]
            else:
                color_index = data[2]
            if data[-1]:
                text = data[0][:8]
            else:
                text = ""
            target.setText(text)
            target.updateStyle(self.bar_style_lpt[color_index])

    def update_blp(self, target, *data):
        """Vehicle best laptime"""
        if target.last != data:
            target.last = data
            if data[-1]:
                text = self.set_laptime(data[0])[:8]
            else:
                text = ""
            target.setText(text)
            target.updateStyle(self.bar_style_blp[data[1]])

    def update_pic(self, target, *data):
        """Position in class"""
        if target.last != data:
            target.last = data
            if data[-1]:
                text = f"{data[0]:02d}"
            else:
                text = ""
            if data[2]:  # player
                style = self.bar_style_pic[1]
            elif self.wcfg["show_class_style_for_position_in_class"]:
                style = f"color:{self.wcfg['font_color_position_in_class']};background:{self.set_class_style(data[1])[1]};"
            else:
                style = self.bar_style_pic[0]
            target.setText(text)
            target.updateStyle(style)

    def update_cls(self, target, *data):
        """Vehicle class"""
        if target.last != data:
            target.last = data
            text, bg_color = self.set_class_style(data[0])
            target.setText(text[:self.cls_width])
            target.updateStyle(f"color:{self.wcfg['font_color_class']};background:{bg_color};")

    def update_pit(self, target, *data):
        """Vehicle in pit"""
        if target.last != data:
            target.last = data
            index = data[0]
            if data[1] and index == 0:  # show yellow flag outside pits
                index = 3
            target.setText(self.pit_status_text[index])
            target.updateStyle(self.bar_style_pit[index])

    def update_tcp(self, target, *data):
        """Tyre compound index"""
        if target.last != data:
            target.last = data
            if data[-1]:
                text = f"{select_compound_symbol(data[0])}{select_compound_symbol(data[1])}"
            else:
                text = ""
            target.setText(text)
            target.updateStyle(self.bar_style_tcp[data[2]])

    def update_psc(self, target, *data):
        """Pitstop count"""
        if target.last != data:
            target.last = data
            if data[0] < 0:
                color_index = 3
            elif self.wcfg["show_pit_request"] and data[1]:
                color_index = 2
            elif data[2]:  # highlight player
                color_index = 1
            else:
                color_index = 0
            if not data[-1]:
                text = ""
            elif data[0] == 0:
                text = TEXT_PLACEHOLDER
            else:
                text = f"{data[0]}"
            target.setText(text)
            target.updateStyle(self.bar_style_psc[color_index])

    def update_nrg(self, target, *data):
        """Remaining energy"""
        if target.last != data:
            target.last = data
            ve = data[0]
            if data[1]:  # highlighted player
                color_index = 4
            elif ve <= -1:  # unavailable
                color_index = 0
            elif ve <= 0.1:  # 10% remaining
                color_index = 3
            elif ve <= 0.3:  # 30% remaining
                color_index = 2
            else:
                color_index = 1
            if not data[-1]:
                text = ""
            elif ve <= -1:
                text = "-" * self.nrg_width
            else:
                text = f"{ve:0{self.nrg_width}.{self.nrg_decimals}%}"[:self.nrg_width]
            target.setText(text)
            target.updateStyle(self.bar_style_nrg[color_index])

    def update_dmg(self, target, *data):
        """Vehicle integrity"""
        if target.last != data:
            target.last = data
            hp = int(data[0] * 10)
            if data[1]:  # highlighted player
                color_index = 3
            elif hp >= 10:  # full integrity
                color_index = 0
            elif hp <= 5:  # low
                color_index = 2
            else:  # high
                color_index = 1
            if not data[-1]:
                text = ""
            elif hp >= 10:
                text = TEXT_PLACEHOLDER
            else:
                text = f"{hp:d}"
            target.setText(text)
            target.updateStyle(self.bar_style_dmg[color_index])

    def update_stl(self, target, *data):
        """Stint laps"""
        if target.last != data:
            target.last = data
            if data[-1]:
                stint_laps_done = data[0]
                stint_laps_est = data[1]
                if stint_laps_done <= 0:
                    text_done = "--"
                else:
                    text_done = f"{stint_laps_done:02.0f}"
                if stint_laps_est <= 0:
                    text_est = "--"
                else:
                    text_est = f"{stint_laps_est // 1:02.0f}"
                text = f"{text_done}/{text_est}"
            else:
                text = ""
            target.setText(text)
            target.updateStyle(self.bar_style_stl[data[2]])

    def update_spd(self, target, *data):
        """Speed trap"""
        if target.last != data:
            target.last = data
            if data[-1]:
                text_speed = f"{self.unit_speed(data[0]):.3f}"[:5]
            else:
                text_speed = ""
            target.setText(text_speed)
            target.updateStyle(self.bar_style_spd[data[1]])

    # Additional methods
    def set_qss_lap_difference(self, fg_color, bg_color, plr_fg_color, plr_bg_color):
        """Set style with player & lap difference:
        0 default, 1 player, 2 same lap, 3 behind lap, 4 ahead lap.
        """
        return (
            self.set_qss(  # 0 default
                fg_color=fg_color,
                bg_color=bg_color),
            self.set_qss(  # 1 player
                fg_color=plr_fg_color,
                bg_color=plr_bg_color),
            self.set_qss(  # 2 same lap
                fg_color=self.wcfg["font_color_same_lap"],
                bg_color=bg_color),
            self.set_qss(  # 3 behind lap
                fg_color=self.wcfg["font_color_laps_behind"],
                bg_color=bg_color),
            self.set_qss(  # 4 ahead lap
                fg_color=self.wcfg["font_color_laps_ahead"],
                bg_color=bg_color),
        )

    def set_brand_logo(self, brand_name: str):
        """Set brand logo"""
        if brand_name not in self.pixmap_brandlogo:  # load & cache logo
            self.pixmap_brandlogo[brand_name] = load_brand_logo_file(
                filepath=self.cfg.path.brand_logo,
                filename=brand_name,
                max_width=self.brd_width,
                max_height=self.brd_height,
            )
        return self.pixmap_brandlogo[brand_name]

    def set_class_style(self, class_name: str):
        """Compare vehicle class name with user defined dictionary"""
        style = self.cfg.user.classes.get(class_name)
        if style is not None:
            return style["alias"], style["color"]
        if class_name:
            return class_name, random_color_class(class_name)
        return class_name, self.wcfg["bkg_color_class"]

    @staticmethod
    def set_laptime(laptime, valid: bool = True):
        """Set lap time"""
        if 0 < laptime < MAX_SECONDS:
            if valid:
                return calc.sec2laptime_full(laptime)
            return f"*{calc.sec2laptime_full(laptime)}"
        return TEXT_NOLAPTIME

    @staticmethod
    def set_pittime(inpit, pit_time):
        """Set lap time"""
        if 0 < pit_time < MAX_SECONDS:
            return f"{'PIT' if inpit else 'OUT'}{pit_time: >5.1f}"
        return TEXT_NOLAPTIME


def lap_difference_index(is_lapped, offset=2):
    """Set lap difference as index

    Returns:
        0 = same lap, 1 = behind, 2 = ahead
    """
    return (is_lapped < 0) + (is_lapped > 0) * 2 + offset
