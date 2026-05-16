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
Class Lap Pace Widget
"""

from ..api_control import api
from ..const_common import MAX_SECONDS
from ..module_info import minfo
from ..userfile.heatmap import select_compound_symbol
from ..validator import is_same_session
from ._base import Overlay

MAX_LAP_DIGITS = 3
TYRE_SYMBOL_WIDTH = 1


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout()
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
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.show_brackets = self.wcfg["show_brackets"]
        self.prefix_lap = self.wcfg["prefix_lap"]
        self.separator = self.wcfg["separator"]
        self.show_tyre = self.wcfg["show_tyre"]
        self.mixed_symbol = (self.wcfg["mixed_compound_symbol"] or "X")[:1]
        self.bracket_open = "[" if self.show_brackets else ""
        self.bracket_close = "]" if self.show_brackets else ""
        self.decimals_time = min(max(int(self.wcfg["decimal_places_time"]), 0), 3)
        self.time_width = 4 + (self.decimals_time + 1 if self.decimals_time > 0 else 0)
        tyre_extra = (len(self.separator) + TYRE_SYMBOL_WIDTH) if self.show_tyre else 0
        self.max_text_width = (
            len(self.bracket_open)
            + len(self.prefix_lap)
            + MAX_LAP_DIGITS
            + len(self.separator)
            + self.time_width
            + tyre_extra
            + len(self.bracket_close)
        )
        self.char_width = font_m.width
        self.bar_padx = bar_padx
        self.text_no_data = self._build_placeholder()

        # Single record bar (width auto-resizes per render in _update_record)
        self.bar_record = self.set_rawtext(
            text=self.text_no_data,
            fixed_width=self.char_width * len(self.text_no_data) + bar_padx,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color"],
            bg_color=self.wcfg["background_color"],
            last=None,
        )
        layout.addWidget(self.bar_record, 0, 0)

        # Tracking state
        self._session_id: tuple | None = None
        self._player_class: str = ""
        self._lap_records: dict[int, tuple[float, str]] = {}
        self._last_completed: dict[int, int] = {}

    def _build_placeholder(self) -> str:
        if self.decimals_time > 0:
            time_part = f"-:--.{'-' * self.decimals_time}"
        else:
            time_part = "-:--"
        tyre_part = f"{self.separator}-" if self.show_tyre else ""
        return (
            f"{self.bracket_open}{self.prefix_lap}{'-' * MAX_LAP_DIGITS}"
            f"{self.separator}{time_part}{tyre_part}{self.bracket_close}"
        )

    def timerEvent(self, event):
        """Update fastest lap per class lap"""
        # Reset only on real session change: combo or session-stamp differs,
        # or elapsed-time / completed-laps go backwards (flashback / restart).
        combo_name = api.read.session.combo_name()
        session_id = api.read.session.identifier()
        if self._session_id is None or not is_same_session(combo_name, session_id, self._session_id):
            self._session_id = (combo_name, *session_id)
            self._player_class = ""
            self._lap_records.clear()
            self._last_completed.clear()
        else:
            self._session_id = (combo_name, *session_id)

        player_idx = minfo.vehicles.playerIndex
        if player_idx < 0:
            self._update_record(self.bar_record, None)
            return

        player_data = minfo.vehicles.dataSet[player_idx]
        player_class = player_data.vehicleClass
        player_completed = api.read.lap.completed_laps(player_idx)

        # Also reset on class change or player lap counter going backwards (flashback / restart)
        if (
            player_class != self._player_class
            or player_completed < self._last_completed.get(player_idx, 0)
        ):
            self._player_class = player_class
            self._lap_records.clear()
            self._last_completed.clear()

        if not player_class:
            self._update_record(self.bar_record, None)
            return

        for idx in range(minfo.vehicles.totalVehicles):
            data = minfo.vehicles.dataSet[idx]
            if data.vehicleClass != player_class:
                continue
            cl = api.read.lap.completed_laps(idx)
            prev = self._last_completed.get(idx, 0)
            if cl > prev:
                t = api.read.timing.last_laptime(idx)
                if t > 0:
                    existing_time = self._lap_records.get(cl, (MAX_SECONDS, ""))[0]
                    if t < existing_time:
                        self._lap_records[cl] = (t, self._tyre_symbol(data))
                self._last_completed[idx] = cl

        if not self._last_completed:
            self._update_record(self.bar_record, None)
            return

        display_lap = max(self._last_completed.values())
        if display_lap <= 0:
            self._update_record(self.bar_record, None)
            return

        time_val, tyre_val = self._lap_records.get(display_lap, (0.0, ""))
        self._update_record(self.bar_record, (display_lap, time_val, tyre_val))

    def _tyre_symbol(self, data) -> str:
        compounds = data.tireCompoundName
        if not compounds:
            return "-"
        if len(set(compounds)) > 1:
            return self.mixed_symbol
        symbol = select_compound_symbol(compounds[0]) or "-"
        return symbol[:TYRE_SYMBOL_WIDTH]

    def _update_record(self, target, data):
        """Render record bar; data is None for no-data, else (lap_num, time, tyre)"""
        if target.last != data:
            target.last = data
            if data is None or data[1] <= 0:
                text = self.text_no_data
            else:
                lap_num, lap_time, tyre = data
                text = self._format_text(lap_num, lap_time, tyre)
            if len(text) > self.max_text_width:
                text = text[:self.max_text_width]
            new_width = self.char_width * len(text) + self.bar_padx
            if target.width() != new_width:
                target.setFixedWidth(new_width)
            target.text = text
            target.update()

    def _format_text(self, lap_num: int, lap_time: float, tyre: str) -> str:
        lap_num = max(0, min(lap_num, 999))
        if self.decimals_time > 0:
            sec_format = f"0{3 + self.decimals_time}.{self.decimals_time}f"
            time_str = f"{lap_time // 60:.0f}:{lap_time % 60:{sec_format}}"
        else:
            time_str = f"{lap_time // 60:.0f}:{int(lap_time % 60):02d}"
        tyre_section = f"{self.separator}{(tyre or '-')[:TYRE_SYMBOL_WIDTH]}" if self.show_tyre else ""
        return (
            f"{self.bracket_open}{self.prefix_lap}{lap_num:d}"
            f"{self.separator}{time_str}{tyre_section}{self.bracket_close}"
        )
