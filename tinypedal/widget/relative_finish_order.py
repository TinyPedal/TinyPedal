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
Relative finish order Widget
"""

from math import ceil

from .. import calculation as calc
from ..api_control import api
from ..const_common import (
    ENERGY_TYPE_ID,
    MAX_SECONDS,
    RACELENGTH_TYPE_ID,
    TEXT_PLACEHOLDER,
)
from ..module_info import minfo
from ..units import set_unit_fuel
from ..validator import generator_init
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap_hori=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        layout_reversed = self.wcfg["layout"] != 0
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.char_width = max(self.wcfg["bar_width"], 3)
        bar_width = font_m.width * self.char_width + bar_padx
        self.range_start = max(self.wcfg["near_start_range"], 0)
        self.range_finish = max(self.wcfg["near_finish_range"], 0)
        self.total_slot = min(max(self.wcfg["number_of_prediction"], 0), 10) + 3
        self.leader_pit_time_set = list(self.create_pit_time_set(self.total_slot, "leader"))
        self.player_pit_time_set = list(self.create_pit_time_set(self.total_slot, "player"))
        self.decimals_laps = max(self.wcfg["decimal_places_laps"], 0)
        self.decimals_refill = max(self.wcfg["decimal_places_refill"], 0)
        self.extra_laps = max(self.wcfg["number_of_extra_laps"], 1)
        self.refill_sign = "" if self.wcfg["show_absolute_refilling"] else "+"

        # Config units
        self.unit_fuel = set_unit_fuel(self.cfg.units["fuel_unit"])

        self.gen_leader_pace = calc_laptime_pace(
            self.wcfg["leader_laptime_pace_samples"],
            max(self.wcfg["leader_laptime_pace_margin"], 0.1))

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Leader pit time row
        bar_style_pit_time = self.set_qss(
            fg_color=self.wcfg["font_color_pit_time"],
            bg_color=self.wcfg["bkg_color_pit_time"],
            font_size=int(self.wcfg['font_size'] * 0.8),
        )
        self.bars_pit_leader = self.set_qlabel(
            style=bar_style_pit_time,
            width=bar_width,
            count=self.total_slot,
        )
        for _pit_time, target in zip(self.leader_pit_time_set, self.bars_pit_leader):
            target.setText(f"{_pit_time:.0f}s")
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_pit_leader,
            row_index=0,
            right_to_left=layout_reversed,
        )

        # Player pit time row
        self.bars_pit_player = self.set_qlabel(
            style=bar_style_pit_time,
            width=bar_width,
            count=self.total_slot,
        )
        for _pit_time, target in zip(self.player_pit_time_set, self.bars_pit_player):
            target.setText(f"{_pit_time:.0f}s")
        self.bars_pit_player[0].setText("DIFF")
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_pit_player,
            row_index=3,
            right_to_left=layout_reversed,
        )

        # Leader lap row
        self.leader_lap_color = (
            self.set_qss(
                fg_color=self.wcfg["font_color_leader"],
                bg_color=self.wcfg["bkg_color_leader"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_near_start"],
                bg_color=self.wcfg["bkg_color_leader"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_near_finish"],
                bg_color=self.wcfg["bkg_color_leader"])
        )
        self.bars_lap_leader = self.set_qlabel(
            text=TEXT_PLACEHOLDER,
            style=self.leader_lap_color[0],
            width=bar_width,
            count=self.total_slot,
        )
        self.bars_lap_leader[0].setText("LDR")
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_lap_leader,
            row_index=1,
            right_to_left=layout_reversed,
        )

        # Player lap row
        self.player_lap_color = (
            self.set_qss(
                fg_color=self.wcfg["font_color_player"],
                bg_color=self.wcfg["bkg_color_player"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_near_start"],
                bg_color=self.wcfg["bkg_color_player"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_near_finish"],
                bg_color=self.wcfg["bkg_color_player"])
        )
        self.bars_lap_player = self.set_qlabel(
            text=TEXT_PLACEHOLDER,
            style=self.player_lap_color[0],
            width=bar_width,
            count=self.total_slot,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_lap_player,
            row_index=2,
            right_to_left=layout_reversed,
        )

        # Player refill row
        bar_style_refill = self.set_qss(
            fg_color=self.wcfg["font_color_refill"],
            bg_color=self.wcfg["bkg_color_refill"]
        )
        self.bars_refill = self.set_qlabel(
            text=TEXT_PLACEHOLDER,
            style=bar_style_refill,
            width=bar_width,
            count=self.total_slot,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_refill,
            row_index=4,
            right_to_left=layout_reversed,
        )

        # Player extra lap refill row
        if self.wcfg["show_extra_refilling"]:
            self.bars_refill_extra = self.set_qlabel(
                text=TEXT_PLACEHOLDER,
                style=bar_style_refill,
                width=bar_width,
                count=self.total_slot,
            )
            self.bars_refill_extra[0].setText(f"EX+{self.extra_laps}")
            self.set_grid_layout_table_row(
                layout=layout,
                targets=self.bars_refill_extra,
                row_index=5,
                right_to_left=layout_reversed,
            )

        # Last data
        self.relative_lap_offset = -MAX_SECONDS

    def timerEvent(self, event):
        """Update when vehicle on track"""
        is_lap_type_session = api.read.session.lap_type()
        in_formation = api.read.session.in_formation()
        energy_type = api.read.vehicle.max_virtual_energy()

        leader_index = minfo.vehicles.leaderIndex
        player_index = minfo.vehicles.playerIndex
        leader_lap_into = api.read.lap.progress(leader_index)
        player_lap_into = api.read.lap.progress()

        leader_laptime_pace = self.gen_leader_pace.send(leader_index)
        player_laptime_pace = minfo.delta.lapTimePace

        leader_valid = 0 < leader_laptime_pace < MAX_SECONDS
        player_valid = 0 < player_laptime_pace < MAX_SECONDS

        if is_lap_type_session and leader_valid and player_valid:
            laps_total = api.read.lap.maximum()
            leader_laps_left = laps_total - api.read.lap.completed_laps(leader_index) - leader_lap_into
            player_laps_left = laps_total - api.read.lap.completed_laps() - player_lap_into
            time_left = min(leader_laptime_pace, player_laptime_pace) * leader_laps_left
            laps_diff = player_laps_left - (time_left / player_laptime_pace)
        else:
            time_left = api.read.session.remaining()
            laps_diff = 0

        # Update last pit time slot
        self.leader_pit_time_set[-1] = minfo.vehicles.dataSet[leader_index].pitTimer.elapsed
        self.update_pit_time(self.bars_pit_leader[-1], self.leader_pit_time_set[-1])

        self.player_pit_time_set[-1] = minfo.vehicles.dataSet[player_index].pitTimer.elapsed
        self.update_pit_time(self.bars_pit_player[-1], self.player_pit_time_set[-1])

        # Get remaining fuel/energy & consumption
        consumption = minfo.energy if energy_type else minfo.fuel
        fuel_in_tank = 0 if self.wcfg["show_absolute_refilling"] else consumption.amountCurrent
        fuel_consumption = consumption.estimatedValidConsumption

        # Update lap progress difference & refill type
        self.update_energy_type(self.bars_refill[0], energy_type)
        self.update_race_type(self.bars_pit_leader[0], is_lap_type_session)
        lap_diff = calc.lap_progress_difference(leader_laptime_pace, player_laptime_pace)
        self.update_lap_int(self.bars_lap_player[0], lap_diff)

        # Update slots
        for index in range(1, self.total_slot):
            # Predicate player
            if not player_valid:
                lap_final, player_hi_range, full_laps_left = -MAX_SECONDS, 0, 0
            elif is_lap_type_session and index > 1:
                lap_final = calc.lap_progress_offset(  # relative lap offset based on 0s column
                    player_laptime_pace, self.relative_lap_offset, self.player_pit_time_set[index])
                player_hi_range = self.set_highlight_range(player_laptime_pace, lap_final % 1)
                full_laps_left = 0
            else:  # time-type race
                lap_into_offset = calc.lap_progress_offset(
                    player_laptime_pace, player_lap_into, self.player_pit_time_set[index])
                lap_remaining = calc.end_timer_laps_remain(
                    lap_into_offset, player_laptime_pace, time_left)
                lap_final = lap_remaining % 1
                player_hi_range = self.set_highlight_range(player_laptime_pace, lap_final)
                full_laps_left = calc.time_type_laps_remain(ceil(lap_remaining), player_lap_into)
            self.update_lap_player(self.bars_lap_player[index], lap_final, player_hi_range)

            if index == 1:  # store relative lap offset
                self.relative_lap_offset = lap_final

            # Player refill
            if (is_lap_type_session and index != 1
                or in_formation or not leader_valid or not player_valid):
                refill_player = -MAX_SECONDS
            else:
                refill_player = calc.total_fuel_needed(
                    full_laps_left,
                    fuel_consumption,
                    fuel_in_tank,
                )
            self.update_refill(self.bars_refill[index], refill_player, energy_type)

            # Player refill extra
            if self.wcfg["show_extra_refilling"]:
                if refill_player == -MAX_SECONDS:
                    refill_extra = -MAX_SECONDS
                else:
                    refill_extra = calc.total_fuel_needed(
                        full_laps_left + self.extra_laps,  # add extra laps
                        fuel_consumption,
                        fuel_in_tank,
                    )
                self.update_refill(self.bars_refill_extra[index], refill_extra, energy_type)

            # Predicate leader
            if not leader_valid or player_index == leader_index:
                leader_lap_final, leader_hi_range = -MAX_SECONDS, 0
            elif is_lap_type_session:
                # Lap-type final lap progress + lap difference from leader
                # Round up laps difference for relative final lap progress against player
                leader_lap_final = calc.lap_progress_offset(
                    leader_laptime_pace, ceil(laps_diff), self.leader_pit_time_set[index])
                leader_hi_range = self.set_highlight_range(
                    leader_laptime_pace, leader_lap_final % 1)
            else:  # time-type race
                leader_lap_into_offset = calc.lap_progress_offset(
                    leader_laptime_pace, leader_lap_into, self.leader_pit_time_set[index])
                leader_lap_remaining = calc.end_timer_laps_remain(
                    leader_lap_into_offset, leader_laptime_pace, time_left)
                leader_lap_final = leader_lap_remaining % 1
                leader_hi_range = self.set_highlight_range(
                    leader_laptime_pace, leader_lap_final)
            self.update_lap_leader(
                self.bars_lap_leader[index], leader_lap_final, leader_hi_range)

    # GUI update methods
    def update_lap_leader(self, target, data, highlight):
        """Leader final lap progress"""
        if target.last != data:
            target.last = data
            if data > -MAX_SECONDS:
                lap_text = f"{data:.{self.decimals_laps}f}"[:self.char_width]
            else:
                lap_text = TEXT_PLACEHOLDER
            target.setText(lap_text)
            target.updateStyle(self.leader_lap_color[highlight])

    def update_lap_player(self, target, data, highlight):
        """Player final lap progress"""
        if target.last != data:
            target.last = data
            if data > -MAX_SECONDS:
                lap_text = f"{data:.{self.decimals_laps}f}"[:self.char_width]
            else:
                lap_text = TEXT_PLACEHOLDER
            target.setText(lap_text)
            target.updateStyle(self.player_lap_color[highlight])

    def update_lap_int(self, target, data):
        """Lap progress difference"""
        if target.last != data:
            target.last = data
            if 0 < data:
                lap_text = f"{data:.{self.decimals_laps}f}"[:self.char_width]
            else:
                lap_text = TEXT_PLACEHOLDER
            target.setText(lap_text)

    def update_pit_time(self, target, data):
        """Leader or player pit time"""
        if target.last != data:
            target.last = data
            target.setText(f"{data:.0f}s")

    def update_race_type(self, target, data):
        """Race type"""
        if target.last != data:
            target.last = data
            target.setText(RACELENGTH_TYPE_ID[data])

    def update_energy_type(self, target, data):
        """Energy type"""
        if target.last != data:
            target.last = data
            target.setText(ENERGY_TYPE_ID[data > 0])

    def update_refill(self, target, data, energy_type):
        """Player refill"""
        if target.last != data:
            target.last = data
            if data > -MAX_SECONDS:
                if not energy_type:
                    data = self.unit_fuel(data)
                refill_text = f"{data:{self.refill_sign}.{self.decimals_refill}f}"[:self.char_width].strip(".")
            else:
                refill_text = TEXT_PLACEHOLDER
            target.setText(refill_text)

    # Additional methods
    def create_pit_time_set(self, total_slot, suffix):
        """Create pit time set"""
        yield 0  # reserved first 2 slots
        yield 0
        for index in range(total_slot - 3):
            yield max(self.wcfg[f"prediction_{index + 1}_{suffix}_pit_time"], 0)
        yield 0  # reserved last slot

    def set_highlight_range(self, laptime_pace, lap_final):
        """Final lap highlight range"""
        if laptime_pace > 0:
            range_limit = laptime_pace / 3  # limit max range to 1/3 of laptime pace
            if lap_final < min(self.range_start, range_limit) / laptime_pace:
                return 1  # near start
            if lap_final > 1 - min(self.range_finish, range_limit) / laptime_pace:
                return -1  # near finish
        return 0


@generator_init
def calc_laptime_pace(samples: int = 6, margin: float = 5, laptime: float = MAX_SECONDS):
    """Calculate lap time pace for specific player"""
    laptime_pace = laptime
    laptime_margin = margin
    ema_factor = calc.ema_factor(samples)
    last_vehicle_class = ""
    last_lap_stime = -1.0
    is_pit_lap = 0  # whether pit in or pit out lap
    validating = 0.0

    while True:
        player_index = yield laptime_pace
        # Calculate laptime pace
        lap_stime = api.read.timing.start(player_index)
        veh_class = api.read.vehicle.class_name(player_index)
        is_pit_lap |= api.read.vehicle.in_pits(player_index)

        # Reset if vehicle class changes
        if last_vehicle_class != veh_class:
            last_vehicle_class = veh_class
            laptime_pace = api.read.timing.reference_laptime(player_index)

        if last_lap_stime != lap_stime:
            last_lap_stime = lap_stime
            validating = api.read.timing.elapsed()
            is_pit_lap = 0

        if validating:
            timer = api.read.timing.elapsed() - validating
            laptime_last = api.read.timing.last_laptime(player_index)
            if 1 < timer <= 10 and 0 < laptime_last:
                if not is_pit_lap:
                    if laptime_pace > laptime_last:
                        laptime_pace = laptime_last
                    else:
                        laptime_pace = min(
                            calc.exp_mov_avg(ema_factor, laptime_pace, laptime_last),
                            laptime_pace + laptime_margin,
                        )
                elif laptime_pace >= MAX_SECONDS:
                    laptime_pace = api.read.timing.reference_laptime(player_index)
                validating = 0
            elif timer > 10:  # switch off after 10s
                validating = 0
