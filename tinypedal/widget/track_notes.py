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
Track notes Widget
"""

from ..api_control import api
from ..const_common import TEXT_NOTAVAILABLE
from ..module_info import minfo
from ..userfile.track_notes import COLUMN_COMMENT, COLUMN_DISTANCE, COLUMN_TRACKNOTE
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        notes_width = max(int(self.wcfg["track_notes_width"]), 1)
        comments_width = max(int(self.wcfg["comments_width"]), 1)
        debugging_width = max(int(self.wcfg["debugging_width"]), 1)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )
        if self.wcfg["show_background"]:
            bg_color_notes = self.wcfg["bkg_color_track_notes"]
            bg_color_comments = self.wcfg["bkg_color_comments"]
            bg_color_debugging = self.wcfg["bkg_color_debugging"]
        else:
            bg_color_notes = ""
            bg_color_comments = ""
            bg_color_debugging = ""

        # Track notes
        if self.wcfg["show_track_notes"]:
            bar_style_notes = self.set_qss(
                fg_color=self.wcfg["font_color_track_notes"],
                bg_color=bg_color_notes
            )
            self.bar_notes = self.set_qlabel(
                text="TRACK NOTES",
                style=bar_style_notes,
                width=font_m.width * notes_width + bar_padx,
                align=self.wcfg["track_notes_text_alignment"],
            )
            self.set_primary_orient(
                target=self.bar_notes,
                column=self.wcfg["column_index_track_notes"],
            )

        # Comments
        if self.wcfg["show_comments"]:
            bar_style_comments = self.set_qss(
                fg_color=self.wcfg["font_color_comments"],
                bg_color=bg_color_comments
            )
            self.bar_comments = self.set_qlabel(
                text="COMMENTS",
                style=bar_style_comments,
                width=font_m.width * comments_width + bar_padx,
                align=self.wcfg["comments_text_alignment"],
            )
            self.set_primary_orient(
                target=self.bar_comments,
                column=self.wcfg["column_index_comments"],
            )

        # Debugging info
        if self.wcfg["show_debugging"]:
            bar_style_debugging = self.set_qss(
                fg_color=self.wcfg["font_color_debugging"],
                bg_color=bg_color_debugging
            )
            self.bar_debugging = self.set_qlabel(
                text="DEBUGGING",
                style=bar_style_debugging,
                width=font_m.width * debugging_width + bar_padx,
                align=self.wcfg["debugging_text_alignment"],
            )
            self.set_primary_orient(
                target=self.bar_debugging,
                column=self.wcfg["column_index_debugging"],
            )

        # Last data
        self.last_notes_index = None
        self.last_auto_hide = False
        self.last_etime = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        pit_override = self.wcfg["show_pit_notes_while_in_pit"] and api.read.vehicle.in_pits()

        if pit_override or api.read.vehicle.in_garage():
            self.update_auto_hide(False)
        elif minfo.tracknotes.currentNote:
            if self.wcfg["maximum_display_duration"] <= 0:
                self.update_auto_hide(False)
            else:
                etime = api.read.timing.elapsed()
                notes_index = minfo.tracknotes.currentIndex
                if self.last_notes_index != notes_index:
                    self.last_notes_index = notes_index
                    self.last_etime = etime
                if self.last_etime > etime:
                    self.last_etime = etime
                self.update_auto_hide(
                    etime - self.last_etime > self.wcfg["maximum_display_duration"])
        elif self.wcfg["auto_hide_if_not_available"]:
            self.update_auto_hide(True)

        if self.wcfg["show_track_notes"]:
            if pit_override:
                notes = self.wcfg["pit_notes_text"]
            else:
                notes = minfo.tracknotes.currentNote.get(COLUMN_TRACKNOTE, TEXT_NOTAVAILABLE)
            self.update_notes(self.bar_notes, notes)

        if self.wcfg["show_comments"]:
            if pit_override:
                comments = self.wcfg["pit_comments_text"]
            else:
                comments = minfo.tracknotes.currentNote.get(COLUMN_COMMENT, TEXT_NOTAVAILABLE)
            self.update_comments(self.bar_comments, comments)

        if self.wcfg["show_debugging"]:
            if pit_override:
                debugging = TEXT_NOTAVAILABLE
            else:
                debugging = minfo.tracknotes.currentNote.get(COLUMN_DISTANCE, TEXT_NOTAVAILABLE)
            self.update_debugging(self.bar_debugging, debugging)

    # GUI update methods
    def update_notes(self, target, data):
        """Track notes"""
        if target.last != data:
            target.last = data
            if self.wcfg["track_notes_uppercase"]:
                data = data.upper()
            target.setText(data)

    def update_comments(self, target, data):
        """Comments"""
        if target.last != data:
            target.last = data
            if self.wcfg["enable_comments_line_break"]:
                data = data.replace("\\n", "\n")
            target.setText(data)

    def update_debugging(self, target, data):
        """Debugging info"""
        if target.last != data:
            target.last = data
            if data != TEXT_NOTAVAILABLE:
                data = (
                    f"IDX:{minfo.tracknotes.currentIndex + 1} "
                    f"POS:{data:.0f}>>{minfo.tracknotes.nextNote.get(COLUMN_DISTANCE, 0):.0f}m"
                )
            target.setText(data)

    def update_auto_hide(self, auto_hide):
        """Auto hide"""
        if self.last_auto_hide != auto_hide:
            self.last_auto_hide = auto_hide
            if self.wcfg["show_track_notes"]:
                self.bar_notes.setHidden(auto_hide)
            if self.wcfg["show_comments"]:
                self.bar_comments.setHidden(auto_hide)
            if self.wcfg["show_debugging"]:
                self.bar_debugging.setHidden(auto_hide)
