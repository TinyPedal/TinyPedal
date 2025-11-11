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
Standings Widget
"""

from .. import calculation as calc
from ..api_control import api
from ..const_common import TEXT_NOLAPTIME, TEXT_PLACEHOLDER
from ..formatter import random_color_class, shorten_driver_name
from ..module_info import minfo
from ..userfile.brand_logo import load_brand_logo_file
from ..userfile.heatmap import select_compound_symbol
from ._base import Overlay
from ._common import ExFrame


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
        self.int_width = max(int(self.wcfg["time_interval_width"]), 1)
        self.gap_decimals = max(int(self.wcfg["time_gap_decimal_places"]), 0)
        self.int_decimals = max(int(self.wcfg["time_interval_decimal_places"]), 0)
        self.show_class_separator = self.wcfg["split_gap"] > 0
        self.show_class_timegap = (self.wcfg["enable_multi_class_split_mode"]
            and self.wcfg["show_time_gap_from_same_class"])
        self.show_class_interval = (self.wcfg["enable_multi_class_split_mode"]
            and self.wcfg["show_time_interval_from_same_class"])
        self.max_delta = calc.asym_max(int(self.wcfg["number_of_delta_laptime"]), 2, 5)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )
        self.bar_split_style = f"margin-top:{self.wcfg['split_gap']}px;max-height:0;"

        # Max display players
        if self.wcfg["enable_multi_class_split_mode"]:
            self.veh_range = min(max(int(self.wcfg["max_vehicles_split_mode"]), 5), 126)
        else:
            self.veh_range = min(max(int(self.wcfg["max_vehicles_combined_mode"]), 5), 126)
        self.pixmap_brandlogo = {}
        self.row_visible = [False] * self.veh_range

        # Driver position
        if self.wcfg["show_position"]:
            self.bar_style_pos = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_position"],
                    bg_color=self.wcfg["bkg_color_position"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_position"],
                    bg_color=self.wcfg["bkg_color_player_position"])
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
                hide_start=1,
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
                hide_start=1,
            )
        # Driver name
        if self.wcfg["show_driver_name"]:
            self.bar_style_drv = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_driver_name"],
                    bg_color=self.wcfg["bkg_color_driver_name"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_driver_name"],
                    bg_color=self.wcfg["bkg_color_player_driver_name"])
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
                hide_start=1,
            )
        # Vehicle name
        if self.wcfg["show_vehicle_name"]:
            self.bar_style_veh = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_vehicle_name"],
                    bg_color=self.wcfg["bkg_color_vehicle_name"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_vehicle_name"],
                    bg_color=self.wcfg["bkg_color_player_vehicle_name"])
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
                hide_start=1,
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
                hide_start=1,
            )
        # Time gap
        if self.wcfg["show_time_gap"]:
            self.bar_style_gap = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_time_gap"],
                    bg_color=self.wcfg["bkg_color_time_gap"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_time_gap"],
                    bg_color=self.wcfg["bkg_color_player_time_gap"])
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
                hide_start=1,
            )
        # Time interval
        if self.wcfg["show_time_interval"]:
            self.bar_style_int = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_time_interval"],
                    bg_color=self.wcfg["bkg_color_time_interval"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_time_interval"],
                    bg_color=self.wcfg["bkg_color_player_time_interval"])
            )
            self.bars_int = self.set_qlabel(
                style=self.bar_style_int[0],
                width=self.int_width * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_int,
                column_index=self.wcfg["column_index_timeinterval"],
                hide_start=1,
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
                hide_start=1,
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
                hide_start=1,
            )
        # Delta laptime
        if self.wcfg["show_delta_laptime"]:
            self.bar_style_dlt_delta = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_delta_laptime"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_delta_laptime_gain"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_delta_laptime_loss"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_delta_laptime"]),
            )
            self.bar_style_dlt = (
                self.set_qss(
                    bg_color=self.wcfg["bkg_color_delta_laptime"]),
                self.set_qss(
                    bg_color=self.wcfg["bkg_color_player_delta_laptime"])
            )
            self.bars_dlt = tuple(
                self.set_delta_table(
                    width=4 * font_m.width,
                    columns=self.max_delta,
                    bar_padx=bar_padx // 2,
                ) for _ in range(self.veh_range)
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_dlt,
                column_index=self.wcfg["column_index_delta_laptime"],
                hide_start=1,
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
                hide_start=1,
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
                hide_start=1,
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
                hide_start=1,
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
                hide_start=1,
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
                hide_start=1,
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
                width=3 * font_m.width + bar_padx,
                count=self.veh_range,
            )
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_nrg,
                column_index=self.wcfg["column_index_energy_remaining"],
                hide_start=1,
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
                hide_start=1,
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
                hide_start=1,
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        standings_list = minfo.relative.standings
        total_std_idx = len(standings_list) - 1  # skip final -1 index
        player_idx = minfo.vehicles.playerIndex
        plr_veh_info = minfo.vehicles.dataSet[player_idx]
        in_race = api.read.session.in_race()

        # Standings update
        for idx in range(self.veh_range):

            if idx < total_std_idx:
                std_idx = standings_list[idx]
            else:
                std_idx = -2

            # Set row state: 0 - show, 1 - draw gap, 2 - hide
            if std_idx >= -1:
                self.row_visible[idx] = True
                state = (std_idx == -1)
            elif not self.row_visible[idx]:
                continue  # skip update if already empty
            else:
                self.row_visible[idx] = False
                state = 2

            # Get vehicle dataset
            veh_info = minfo.vehicles.dataSet[std_idx]
            # Highlighted player
            hi_player = self.wcfg["show_player_highlighted"] and veh_info.isPlayer
            # Driver position
            if self.wcfg["show_position"]:
                self.update_pos(self.bars_pos[idx], veh_info.positionOverall, hi_player, state)
            # Driver position change
            if self.wcfg["show_position_change"]:
                if self.wcfg["show_position_change_in_class"]:
                    pos_diff = veh_info.qualifyInClass - veh_info.positionInClass
                else:
                    pos_diff = veh_info.qualifyOverall - veh_info.positionOverall
                self.update_pgl(self.bars_pgl[idx], pos_diff, hi_player, state)
            # Driver name
            if self.wcfg["show_driver_name"]:
                self.update_drv(self.bars_drv[idx], veh_info.driverName, hi_player, state)
            # Vehicle name
            if self.wcfg["show_vehicle_name"]:
                self.update_veh(self.bars_veh[idx], veh_info.vehicleName, hi_player, state)
            # Brand logo
            if self.wcfg["show_brand_logo"]:
                self.update_brd(self.bars_brd[idx], veh_info.vehicleName, hi_player, state)
            # Time gap
            if self.wcfg["show_time_gap"]:
                if in_race:
                    if self.show_class_timegap:
                        time_gap = self.gap_to_leader_race(veh_info.gapBehindLeaderInClass, veh_info.positionInClass)
                    else:
                        time_gap = self.gap_to_leader_race(veh_info.gapBehindLeader, veh_info.positionOverall)
                else:
                    if self.show_class_timegap:
                        time_gap = self.gap_to_leader_best(veh_info.bestLapTime, veh_info.classBestLapTime)
                    else:
                        time_gap = self.gap_to_leader_best(veh_info.bestLapTime, minfo.vehicles.leaderBestLapTime)
                self.update_gap(self.bars_gap[idx], time_gap, hi_player, state)
            # Time interval
            if self.wcfg["show_time_interval"]:
                if self.show_class_interval:
                    time_int = (veh_info.positionInClass, veh_info.gapBehindNextInClass)
                else:
                    time_int = (veh_info.positionOverall, veh_info.gapBehindNext)
                self.update_int(self.bars_int[idx], time_int, hi_player, state)
            # Vehicle laptime
            if self.wcfg["show_laptime"]:
                if in_race or self.wcfg["show_best_laptime"]:
                    if veh_info.pitTimer.pitting:
                        laptime = self.set_pittime(veh_info.inPit, veh_info.pitTimer.elapsed)
                        is_class_best = False
                    else:
                        laptime = self.set_laptime(veh_info.lastLapTime)
                        is_class_best = veh_info.isClassFastestLastLap
                else:
                    laptime = self.set_laptime(veh_info.bestLapTime)
                    is_class_best = False
                self.update_lpt(self.bars_lpt[idx], laptime, is_class_best, hi_player, state)
            # Vehicle best laptime
            if self.wcfg["show_best_laptime"]:
                self.update_blp(self.bars_blp[idx], veh_info.bestLapTime, hi_player, state)
            # Position in class
            if self.wcfg["show_position_in_class"]:
                self.update_pic(self.bars_pic[idx], veh_info.positionInClass, hi_player, state)
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
                self.update_psc(self.bars_psc[idx], veh_info.numPitStops, veh_info.pitState, hi_player, state)
            # Delta laptime
            if self.wcfg["show_delta_laptime"]:
                delta_laptime = tuple(veh_info.lapTimeHistory.delta(plr_veh_info.lapTimeHistory, self.max_delta))
                self.update_dlt(self.bars_dlt[idx], delta_laptime, hi_player, state)
            # Remaining energy
            if self.wcfg["show_energy_remaining"]:
                self.update_nrg(self.bars_nrg[idx], veh_info.energyRemaining, hi_player, state)
            # Vehicle integrity
            if self.wcfg["show_vehicle_integrity"]:
                self.update_dmg(self.bars_dmg[idx], veh_info.vehicleIntegrity, hi_player, state)
            # Stint laps
            if self.wcfg["show_stint_laps"]:
                self.update_stl(self.bars_stl[idx], veh_info.currentStintLaps, veh_info.estimatedStintLaps, hi_player, state)

    # GUI update methods
    def update_pos(self, target, *data):
        """Driver position"""
        if target.last != data:
            target.last = data
            target.setText(f"{data[0]:02d}")
            target.updateStyle(self.bar_style_pos[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_pgl(self, target, *data):
        """Driver position change (gain/loss)"""
        if target.last != data:
            target.last = data
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
            target.setText(text)
            target.updateStyle(self.bar_style_pgl[color_index])
            self.toggle_visibility(target, data[-1])

    def update_drv(self, target, *data):
        """Driver name"""
        if target.last != data:
            target.last = data
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
            target.setText(text)
            target.updateStyle(self.bar_style_drv[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_veh(self, target, *data):
        """Vehicle name"""
        if target.last != data:
            target.last = data
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
            target.setText(text)
            target.updateStyle(self.bar_style_veh[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_brd(self, target, *data):
        """Brand logo"""
        if target.last != data:
            target.last = data
            target.setPixmap(self.set_brand_logo(self.cfg.user.brands.get(data[0], data[0])))
            target.updateStyle(self.bar_style_brd[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_gap(self, target, *data):
        """Time gap"""
        if target.last != data:
            target.last = data
            target.setText(data[0][:self.gap_width].strip("."))
            target.updateStyle(self.bar_style_gap[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_int(self, target, *data):
        """Time interval"""
        if target.last != data:
            target.last = data
            target.setText(self.int_to_next(*data[0])[:self.int_width].strip("."))
            target.updateStyle(self.bar_style_int[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_lpt(self, target, *data):
        """Vehicle laptime"""
        if target.last != data:
            target.last = data
            if self.wcfg["show_highlighted_fastest_last_laptime"] and data[1]:
                color_index = 2 + data[2]
            else:
                color_index = data[2]
            target.setText(data[0])
            target.updateStyle(self.bar_style_lpt[color_index])
            self.toggle_visibility(target, data[-1])

    def update_blp(self, target, *data):
        """Vehicle best laptime"""
        if target.last != data:
            target.last = data
            target.setText(self.set_best_laptime(data[0]))
            target.updateStyle(self.bar_style_blp[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_dlt(self, target, *data):
        """Vehicle delta laptime"""
        if target.last != data:
            target.last = data
            is_player = data[1]
            for bar_delta, delta in zip(target.bar_set, data[0]):
                if -999 < delta < 0:  # player time gain
                    text = f"{-delta:.1f}"[:3].strip(".")
                    color_index = 1
                elif 0 < delta < 999:  # player time loss
                    text = f"{delta:.1f}"[:3].strip(".")
                    color_index = 2
                elif delta == 0:
                    text = "0.0"
                    color_index = 0
                else:
                    text = "-.-"
                    color_index = 0
                if is_player:
                    color_index = -1
                bar_delta.setText(text)
                bar_delta.updateStyle(self.bar_style_dlt_delta[color_index])
            target.updateStyle(self.bar_style_dlt[is_player])
            self.toggle_visibility_delta(target, data[-1])

    def update_pic(self, target, *data):
        """Position in class"""
        if target.last != data:
            target.last = data
            target.setText(f"{data[0]:02d}")
            target.updateStyle(self.bar_style_pic[data[1]])
            self.toggle_visibility(target, data[-1])

    def update_cls(self, target, *data):
        """Vehicle class"""
        if target.last != data:
            target.last = data
            text, bg_color = self.set_class_style(data[0])
            target.setText(text[:self.cls_width])
            target.updateStyle(f"color:{self.wcfg['font_color_class']};background:{bg_color};")
            self.toggle_visibility(target, data[-1])

    def update_pit(self, target, *data):
        """Vehicle in pit"""
        if target.last != data:
            target.last = data
            index = data[0]
            if data[1] and index == 0:  # show yellow flag outside pits
                index = 3
            target.setText(self.pit_status_text[index])
            target.updateStyle(self.bar_style_pit[index])
            self.toggle_visibility(target, data[-1])

    def update_tcp(self, target, *data):
        """Tyre compound index"""
        if target.last != data:
            target.last = data
            target.setText(f"{select_compound_symbol(data[0])}{select_compound_symbol(data[1])}")
            target.updateStyle(self.bar_style_tcp[data[2]])
            self.toggle_visibility(target, data[-1])

    def update_psc(self, target, *data):
        """Pitstop count"""
        if target.last != data:
            target.last = data
            if data[0] < 0:
                color_index = 3
            elif self.wcfg["show_pit_request"] and data[1]:
                color_index = 2
            elif data[2]:  # highlighted player
                color_index = 1
            else:
                color_index = 0
            if data[0] == 0:
                text = TEXT_PLACEHOLDER
            else:
                text = f"{data[0]}"
            target.setText(text)
            target.updateStyle(self.bar_style_psc[color_index])
            self.toggle_visibility(target, data[-1])

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
            if ve <= -1:
                text = "---"
            else:
                text = f"{ve:03.0%}"[:3]
            target.setText(text)
            target.updateStyle(self.bar_style_nrg[color_index])
            self.toggle_visibility(target, data[-1])

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
            if hp >= 10:
                text = TEXT_PLACEHOLDER
            else:
                text = f"{hp:d}"
            target.setText(text)
            target.updateStyle(self.bar_style_dmg[color_index])
            self.toggle_visibility(target, data[-1])

    def update_stl(self, target, *data):
        """Stint laps"""
        if target.last != data:
            target.last = data
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
            target.setText(f"{text_done}/{text_est}")
            target.updateStyle(self.bar_style_stl[data[2]])
            self.toggle_visibility(target, data[-1])

    # Additional methods
    def toggle_visibility(self, target, state):
        """Hide bar if unavailable"""
        if state == 0:
            target.show()
        elif state == 1 and self.show_class_separator:  # draw gap
            target.clear()
            target.updateStyle(self.bar_split_style)
            target.show()
        else:
            target.hide()

    def toggle_visibility_delta(self, target, state):
        """Hide bar if unavailable"""
        if state == 0:
            target.show()
        elif state == 1 and self.show_class_separator:  # draw gap
            for _bar in target.bar_set:
                _bar.clear()
            target.updateStyle(self.bar_split_style)
            target.show()
        else:
            target.hide()

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
        if class_name and self.wcfg["show_random_color_for_unknown_class"]:
            return class_name, random_color_class(class_name)
        return class_name, self.wcfg["bkg_color_class"]

    @staticmethod
    def set_laptime(laptime):
        """Set lap time"""
        if laptime <= 0:
            return TEXT_NOLAPTIME
        return calc.sec2laptime_full(laptime)[:8]

    @staticmethod
    def set_pittime(inpit, pit_time):
        """Set lap time"""
        if pit_time <= 0:
            return TEXT_NOLAPTIME
        return f"{'PIT' if inpit else 'OUT'}{pit_time: >5.1f}"[:8]

    @staticmethod
    def set_best_laptime(laptime_best):
        """Set best lap time"""
        if laptime_best <= 0:
            return TEXT_NOLAPTIME
        return calc.sec2laptime_full(laptime_best)[:8]

    def gap_to_leader_best(self, player_best, leader_best):
        """Gap to leader's best laptime"""
        time = player_best - leader_best  # leader best
        if time == 0 and player_best > 0:
            return self.wcfg["time_gap_leader_text"]
        if time < 0 or player_best < 1:  # no time set
            return "0.0"
        return f"{time:.{self.gap_decimals}f}"

    def gap_to_leader_race(self, gap_behind, position):
        """Gap to race leader"""
        if position == 1:
            return self.wcfg["time_gap_leader_text"]
        if isinstance(gap_behind, int):
            return f"{gap_behind:.0f}L"
        return f"{gap_behind:.{self.gap_decimals}f}"

    def int_to_next(self, position, gap_behind):
        """Interval to next"""
        if position == 1:
            return self.wcfg["time_interval_leader_text"]
        if isinstance(gap_behind, int):
            return f"{gap_behind:.0f}L"
        return f"{gap_behind:.{self.int_decimals}f}"

    def set_delta_table(self, width: int, columns: int, bar_padx: int) -> ExFrame:
        """Set delta laptime table"""
        bar_temp = ExFrame(self)
        layout = self.set_grid_layout()
        layout.setContentsMargins(bar_padx, 0, bar_padx, 0)
        bar_temp.setLayout(layout)
        bar_temp.updateStyle(self.bar_style_dlt[0])
        bar_temp.bar_set = self.set_qlabel(
            fixed_width=width,
            count=columns,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=bar_temp.bar_set,
            right_to_left=self.wcfg["show_inverted_delta_laptime_layout"],
        )
        return bar_temp
