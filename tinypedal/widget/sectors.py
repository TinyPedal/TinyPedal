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
Sectors Widget
"""

from .. import calculation as calc
from ..api_control import api
from ..const_common import MAX_SECONDS, PREV_SECTOR_INDEX, SECTOR_ABBR_ID
from ..module_info import minfo
from ..validator import valid_sectors
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        bar_gap = self.wcfg["bar_gap"]
        layout = self.set_grid_layout(gap=bar_gap)
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        if self.wcfg["target_laptime"] == "Theoretical":
            self.prefix_best = "TB"
        else:
            self.prefix_best = "PB"

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Target time
        layout_laptime = self.set_grid_layout(gap=bar_gap)
        self.bar_style_time_target = (
            self.set_qss(
                fg_color=self.wcfg["font_color_time_loss"],
                bg_color=self.wcfg["bkg_color_target_time"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_time_gain"],
                bg_color=self.wcfg["bkg_color_target_time"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_target_time"],
                bg_color=self.wcfg["bkg_color_target_time"])
        )
        self.bar_time_target = self.set_qlabel(
            text="  --:--.---",
            style=self.bar_style_time_target[2],
            width=font_m.width * 11 + bar_padx,
        )
        layout_laptime.addWidget(self.bar_time_target, 0, 0)

        # Current time
        bar_style_time_curr = self.set_qss(
            fg_color=self.wcfg["font_color_current_time"],
            bg_color=self.wcfg["bkg_color_current_time"]
        )
        self.bar_time_curr = self.set_qlabel(
            text="  --:--.---",
            style=bar_style_time_curr,
            width=font_m.width * 11 + bar_padx,
        )
        layout_laptime.addWidget(self.bar_time_curr, 0, 1)

        # Gap to best sector time
        layout_sector = self.set_grid_layout(gap=bar_gap)
        self.bar_style_gap = (
            self.set_qss(
                fg_color=self.wcfg["font_color_sector_highlighted"],
                bg_color=self.wcfg["bkg_color_time_loss"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_sector_highlighted"],
                bg_color=self.wcfg["bkg_color_time_gain"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_sector"],
                bg_color=self.wcfg["bkg_color_sector"]),
        )
        self.bars_time_gap = self.set_qlabel(
            style=self.bar_style_gap[2],
            width=font_m.width * 7 + bar_padx,
            count=3,
        )
        for idx, bar_time_gap in enumerate(self.bars_time_gap):
            bar_time_gap.setText(SECTOR_ABBR_ID[idx])
            layout_sector.addWidget(bar_time_gap, 0, idx)

        # Set layout
        if self.wcfg["layout"] == 0:  # sector time above delta
            layout.addLayout(layout_laptime, 0, 1)
            layout.addLayout(layout_sector, 1, 1)
        else:
            layout.addLayout(layout_laptime, 1, 1)
            layout.addLayout(layout_sector, 0, 1)

        # Last data
        self.last_sector_idx = -1  # previous recorded sector index value
        self.last_target_time = MAX_SECONDS
        self.freeze_timer_start = 0  # sector timer start

    def post_update(self):
        self.last_sector_idx = -1
        self.last_target_time = MAX_SECONDS
        self.freeze_timer_start = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Read Sector data
        lap_stime = api.read.timing.start()
        lap_etime = api.read.timing.elapsed()
        laptime_curr = max(lap_etime - lap_stime, 0)
        data = minfo.sectors

        # Triggered when sector changed
        if self.last_sector_idx != data.sectorIndex:

            # Activate freeze timer, reset sector index
            self.freeze_timer_start = lap_etime
            self.last_sector_idx = data.sectorIndex

            # Previous sector index
            prev_s_idx = PREV_SECTOR_INDEX[data.sectorIndex]

            # Update (time target) best sector text
            if self.wcfg["target_laptime"] == "Theoretical":
                self.last_target_time = calc.accumulated_sum(data.sectorBestTB, data.sectorIndex)
                self.update_time_target_gap(data.deltaSectorBestTB, prev_s_idx)
                if not data.noDeltaSector:
                    self.update_sector_gap(
                        self.bars_time_gap[prev_s_idx],
                        data.deltaSectorBestTB[prev_s_idx],
                    )
            else:
                self.last_target_time = calc.accumulated_sum(data.sectorBestPB, data.sectorIndex)
                self.update_time_target_gap(data.deltaSectorBestPB, prev_s_idx)
                if not data.noDeltaSector:
                    self.update_sector_gap(
                        self.bars_time_gap[prev_s_idx],
                        data.deltaSectorBestPB[prev_s_idx],
                    )

            # Freeze previous sector time
            if valid_sectors(data.sectorPrev[prev_s_idx]):  # valid previous sector time
                sum_sectortime = calc.accumulated_sum(data.sectorPrev, prev_s_idx)
                if sum_sectortime < MAX_SECONDS:  # bypass invalid value
                    laptime_curr = sum_sectortime
            self.update_time_curr(self.bar_time_curr, laptime_curr, prev_s_idx)

        # Update freeze timer
        if self.freeze_timer_start:
            # Stop freeze timer after duration
            freeze_time = self.freeze_duration(data.sectorPrev[data.sectorIndex])
            if lap_etime - self.freeze_timer_start >= freeze_time:
                self.freeze_timer_start = 0  # stop timer
                # Update target time
                self.update_time_target(self.last_target_time)
                # Restore best sector time when cross finish line
                if data.sectorIndex == 0:
                    if self.wcfg["target_laptime"] == "Theoretical":
                        self.restore_best_sector(data.sectorBestTB)
                    else:
                        self.restore_best_sector(data.sectorBestPB)
        else:
            # Update current sector time
            self.update_time_curr(self.bar_time_curr, laptime_curr, data.sectorIndex)

    # GUI update methods
    def update_sector_gap(self, target, data):
        """Gap to best sector time"""
        if target.last != data:
            target.last = data
            target.setText(f"{data:+.3f}"[:7])
            target.updateStyle(self.bar_style_gap[data < 0])

    def update_time_curr(self, target, data, prev_s_idx):
        """Current sector time text"""
        if target.last != data:
            target.last = data
            target.setText(f"{SECTOR_ABBR_ID[prev_s_idx]}{calc.sec2laptime(data)[:8]: >9}")

    def update_time_target(self, seconds):
        """Target sector time text"""
        if seconds < MAX_SECONDS:  # bypass invalid value
            text_laptime = f"{self.prefix_best}{calc.sec2laptime(seconds)[:8]: >9}"
        else:
            text_laptime = f"{self.prefix_best}   --.---"
        self.bar_time_target.setText(text_laptime)
        self.bar_time_target.updateStyle(self.bar_style_time_target[2])

    def update_time_target_gap(self, delta_sec, sec_index):
        """Target sector time gap"""
        sector_gap = calc.accumulated_sum(delta_sec, sec_index)
        self.bar_time_target.setText(f"{self.prefix_best}{sector_gap: >+9.3f}"[:11])
        self.bar_time_target.updateStyle(self.bar_style_time_target[sector_gap < 0])

    def restore_best_sector(self, sector_time):
        """Restore best sector time"""
        for idx, bar_time_gap in enumerate(self.bars_time_gap):
            if valid_sectors(sector_time[idx]):
                text_s = f"{sector_time[idx]:.3f}"[:7]
            else:
                text_s = SECTOR_ABBR_ID[idx]
            bar_time_gap.setText(text_s)
            bar_time_gap.updateStyle(self.bar_style_gap[2])

    # Sector data update methods
    def freeze_duration(self, seconds):
        """Set freeze duration"""
        if valid_sectors(seconds):
            max_freeze = seconds * 0.5
        else:
            max_freeze = 3
        return calc.zero_max(self.wcfg["freeze_duration"], max_freeze)
