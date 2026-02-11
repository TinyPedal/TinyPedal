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
Virtual energy Widget
"""

from .. import calculation as calc
from ..module_info import minfo
from ._base import Overlay
from ._common import warning_flash
from ._painter import FuelLevelBar


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        text_def = "-.--"
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.bar_width = max(self.wcfg["bar_width"], 3)
        style_width = font_m.width * self.bar_width + bar_padx
        column_count = 0

        # Create layout
        layout_upper = self.set_grid_layout()
        layout_lower = self.set_grid_layout()
        layout.addLayout(layout_upper, self.wcfg["column_index_upper"], 0)
        layout.addLayout(layout_lower, self.wcfg["column_index_lower"], 0)

        # Caption style
        if self.wcfg["show_caption"]:
            font_cap = self.config_font(
                self.wcfg["font_name"],
                self.wcfg["font_size"] * self.wcfg["font_scale_caption"],
                self.wcfg["font_weight"],
            )
            font_cap_m = self.get_font_metrics(font_cap)

            row_idx_upper = 2 * self.wcfg["swap_upper_caption"]
            row_idx_lower = 2 - 2 * self.wcfg["swap_lower_caption"]

        # Remaining
        self.bar_style_curr = (
            self.wcfg["bkg_color_remain"],
            self.wcfg["warning_color_low_energy"],
        )
        self.bar_curr = self.set_rawtext(
            text=text_def,
            fixed_width=style_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_remain"],
            bg_color=self.bar_style_curr[0],
        )
        self.bar_curr.decimals = max(self.wcfg["decimal_places_remain"], 0)
        layout_upper.addWidget(self.bar_curr, 1, 1)
        column_count += 1

        if self.wcfg["show_caption"]:
            cap_temp = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text_remain"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
            )
            layout_upper.addWidget(cap_temp, row_idx_upper, 1)

        # Total needed
        self.bar_style_need = (
            self.wcfg["bkg_color_refill"],
            self.wcfg["warning_color_low_energy"],
        )
        self.bar_need = self.set_rawtext(
            text=text_def,
            fixed_width=style_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_refill"],
            bg_color=self.bar_style_need[0],
        )
        self.bar_need.decimals = max(self.wcfg["decimal_places_refill"], 0)
        layout_upper.addWidget(self.bar_need, 1, 2)
        column_count += 1

        if self.wcfg["show_caption"]:
            cap_temp = self.set_rawtext(
                font=font_cap,
                text=(
                    self.wcfg["caption_text_absolute_refill"]
                    if self.wcfg["show_absolute_refilling"]
                    else self.wcfg["caption_text_refill"]
                ),
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
            )
            layout_upper.addWidget(cap_temp, row_idx_upper, 2)

        # Estimated laps can last
        self.bar_laps = self.set_rawtext(
            text=text_def,
            fixed_width=style_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_laps"],
            bg_color=self.wcfg["bkg_color_laps"],
        )
        self.bar_laps.decimals = max(self.wcfg["decimal_places_laps"], 0)
        layout_lower.addWidget(self.bar_laps, 1, 1)

        if self.wcfg["show_caption"]:
            cap_temp = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text_laps"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
            )
            layout_lower.addWidget(cap_temp, row_idx_lower, 1)

        # Estimated minutes can last
        self.bar_mins = self.set_rawtext(
            text=text_def,
            fixed_width=style_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_minutes"],
            bg_color=self.wcfg["bkg_color_minutes"],
        )
        self.bar_mins.decimals = max(self.wcfg["decimal_places_minutes"], 0)
        layout_lower.addWidget(self.bar_mins, 1, 2)

        if self.wcfg["show_caption"]:
            cap_temp = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text_minutes"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
            )
            layout_lower.addWidget(cap_temp, row_idx_lower, 2)

        # Estimated consumption
        self.bar_used = self.set_rawtext(
            text=text_def,
            fixed_width=style_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_used"],
            bg_color=self.wcfg["bkg_color_used"],
        )
        self.bar_used.decimals = max(self.wcfg["decimal_places_used"], 0)
        layout_upper.addWidget(self.bar_used, 1, 3)
        column_count += 1

        if self.wcfg["show_caption"]:
            cap_temp = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text_used"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
            )
            layout_upper.addWidget(cap_temp, row_idx_upper, 3)

        # Estimated one less pit consumption
        self.bar_save = self.set_rawtext(
            text=text_def,
            fixed_width=style_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_save"],
            bg_color=self.wcfg["bkg_color_save"],
        )
        self.bar_save.decimals = max(self.wcfg["decimal_places_save"], 0)
        layout_lower.addWidget(self.bar_save, 1, 3)

        if self.wcfg["show_caption"]:
            cap_temp = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text_save"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
            )
            layout_lower.addWidget(cap_temp, row_idx_lower, 3)

        if self.wcfg["show_estimated_pitstop_count"]:
            # Estimate pit stop counts when pitting at end of current stint
            self.bar_pits = self.set_rawtext(
                text=text_def,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_pits"],
                bg_color=self.wcfg["bkg_color_pits"],
            )
            self.bar_pits.decimals = max(self.wcfg["decimal_places_pits"], 0)
            layout_upper.addWidget(self.bar_pits, 1, 0)
            column_count += 1

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_pits"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_upper.addWidget(cap_temp, row_idx_upper, 0)

            # Estimate pit stop counts when pitting at end of current lap
            self.bar_early = self.set_rawtext(
                text=text_def,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_early"],
                bg_color=self.wcfg["bkg_color_early"],
            )
            self.bar_early.decimals = max(self.wcfg["decimal_places_early"], 0)
            layout_lower.addWidget(self.bar_early, 1, 0)

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_early"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_lower.addWidget(cap_temp, row_idx_lower, 0)

        if self.wcfg["show_delta_and_end_remaining"]:
            # Delta consumption
            self.bar_delta = self.set_rawtext(
                text=text_def,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_delta"],
                bg_color=self.wcfg["bkg_color_delta"],
            )
            self.bar_delta.decimals = max(self.wcfg["decimal_places_delta"], 0)
            layout_upper.addWidget(self.bar_delta, 1, 4)
            column_count += 1

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_delta"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_upper.addWidget(cap_temp, row_idx_upper, 4)

            # Estimated end remaining
            self.bar_end = self.set_rawtext(
                text=text_def,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_end"],
                bg_color=self.wcfg["bkg_color_end"],
            )
            self.bar_end.decimals = max(self.wcfg["decimal_places_end"], 0)
            layout_lower.addWidget(self.bar_end, 1, 4)

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_end"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_lower.addWidget(cap_temp, row_idx_lower, 4)

        if self.wcfg["show_fuel_ratio_and_bias"]:
            # Fuel ratio
            self.bar_ratio = self.set_rawtext(
                text=text_def,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_ratio"],
                bg_color=self.wcfg["bkg_color_ratio"],
            )
            self.bar_ratio.decimals = max(self.wcfg["decimal_places_ratio"], 0)
            layout_upper.addWidget(self.bar_ratio, 1, 5)
            column_count += 1

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_ratio"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_upper.addWidget(cap_temp, row_idx_upper, 5)

            # Fuel bias
            self.bar_bias = self.set_rawtext(
                text=text_def,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_bias"],
                bg_color=self.wcfg["bkg_color_bias"],
            )
            self.bar_bias.decimals = max(self.wcfg["decimal_places_bias"], 0)
            layout_lower.addWidget(self.bar_bias, 1, 5)

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_bias"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_lower.addWidget(cap_temp, row_idx_lower, 5)

        # Energy level bar
        if self.wcfg["show_energy_level_bar"]:
            self.bar_level = FuelLevelBar(
                self,
                width=(font_m.width * self.bar_width + bar_padx) * column_count,
                height=max(self.wcfg["energy_level_bar_height"], 1),
                start_mark_width=max(self.wcfg["starting_energy_level_mark_width"], 1),
                refill_mark_width=max(self.wcfg["refilling_level_mark_width"], 1),
                input_color=self.wcfg["highlight_color_energy_level"],
                bg_color=self.wcfg["bkg_color_energy_level"],
                start_mark_color=self.wcfg["starting_energy_level_mark_color"],
                refill_mark_color=self.wcfg["refilling_level_mark_color"],
                show_start_mark=self.wcfg["show_starting_energy_level_mark"],
                show_refill_mark=self.wcfg["show_refilling_level_mark"],
            )
            layout.addWidget(self.bar_level, self.wcfg["column_index_middle"], 0)

        if self.wcfg["show_low_energy_warning_flash"]:
            self.warn_flash = warning_flash(
                self.wcfg["warning_flash_highlight_duration"],
                self.wcfg["warning_flash_interval"],
                self.wcfg["number_of_warning_flashes"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        is_low_energy = minfo.energy.estimatedLaps <= self.wcfg["low_energy_lap_threshold"]
        if self.wcfg["show_low_energy_warning_flash"] and minfo.energy.estimatedValidConsumption:
            is_low_energy = self.warn_flash.send(is_low_energy)
            if is_low_energy:
                padding = 0.00000001  # add padding for switching state
            else:
                padding = 0
        else:
            padding = 0

        # Remaining
        amount_curr = minfo.energy.amountCurrent
        self.update_energy(self.bar_curr, amount_curr + padding, self.bar_style_curr[is_low_energy])

        # Total needed
        if self.wcfg["show_absolute_refilling"]:
            amount_need = calc.sym_max(minfo.energy.neededAbsolute, 9999)
            self.update_energy(self.bar_need, amount_need + padding, self.bar_style_need[is_low_energy])
        else:
            amount_need = calc.sym_max(minfo.energy.neededRelative, 9999)
            self.update_energy(self.bar_need, amount_need + padding, self.bar_style_need[is_low_energy], "+")

        # Estimated laps can last
        est_runlaps = min(minfo.energy.estimatedLaps, 9999)
        self.update_energy(self.bar_laps, est_runlaps)

        # Estimated minutes can last
        est_runmins = min(minfo.energy.estimatedMinutes, 9999)
        self.update_energy(self.bar_mins, est_runmins)

        # Estimated consumption
        used_last = minfo.energy.estimatedConsumption
        self.update_energy(self.bar_used, used_last)

        # Estimated one less pit consumption
        energy_save = calc.zero_max(minfo.energy.oneLessPitConsumption, 99.99)
        self.update_energy(self.bar_save, energy_save)

        if self.wcfg["show_estimated_pitstop_count"]:
            # Estimate pit stop counts when pitting at end of current stint
            est_pits_end = calc.zero_max(minfo.energy.estimatedNumPitStopsEnd, 99.99)
            self.update_energy(self.bar_pits, est_pits_end)

            # Estimate pit stop counts when pitting at end of current lap
            est_pits_early = calc.zero_max(minfo.energy.estimatedNumPitStopsEarly, 99.99)
            self.update_energy(self.bar_early, est_pits_early)

        if self.wcfg["show_delta_and_end_remaining"]:
            # Delta consumption
            delta_energy = minfo.energy.deltaConsumption
            self.update_energy(self.bar_delta, delta_energy, None, "+")

            # Estimated end remaining
            amount_end = minfo.energy.amountEndStint
            self.update_energy(self.bar_end, amount_end)

        if self.wcfg["show_fuel_ratio_and_bias"]:
            # Fuel ratio
            fuel_ratio = minfo.hybrid.fuelEnergyRatio
            self.update_energy(self.bar_ratio, fuel_ratio)

            # Fuel bias
            fuel_bias = minfo.hybrid.fuelEnergyBias
            self.update_energy(self.bar_bias, fuel_bias, None, "+")

        # Energy level bar
        if self.wcfg["show_energy_level_bar"]:
            level_capacity = minfo.energy.capacity
            level_curr = minfo.energy.amountCurrent
            level_start = minfo.energy.amountStart
            level_refill = level_curr + minfo.energy.neededRelative
            level_state = round(level_curr + level_start + level_refill, 3)
            if level_capacity and self.bar_level.last != level_state:
                self.bar_level.last = level_state
                self.bar_level.update_input(
                    level_curr / level_capacity,
                    level_start / level_capacity,
                    level_refill / level_capacity,
                )

    # GUI update methods
    def update_energy(self, target, data, color=None, sign=""):
        """Update energy data"""
        if target.last != data:
            target.last = data
            target.text = f"{data:{sign}.{target.decimals}f}"[:self.bar_width].strip(".")
            if color:  # low energy warning
                target.bg = color
            target.update()
