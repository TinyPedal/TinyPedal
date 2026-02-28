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
Layout manager for config dialog sections.
"""

from __future__ import annotations

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ._common import UIScaler


class ConfigLayout:
    """Manages section arrangement: column reflow, top-area controls, responsive resizing."""

    def __init__(self, builder, grouper, keys, key_name, current_values, has_preview, margin):
        self._builder = builder
        self._grouper = grouper
        self._keys = keys
        self._key_name = key_name
        self._current_values = current_values
        self._has_preview = has_preview
        self._margin = margin

        self.general_frame: QFrame | None = None
        self.column_index_frames: list[QFrame] = []
        self.section_widgets: list[QFrame] = []
        self.sections: list[tuple[str | None, list[str]]] = []

        self._num_columns = 0
        self._widest_section = 0

    def build(self) -> QWidget:
        """Build all sections and return initial scroll content."""
        sections = self._grouper.group_keys(self._keys)
        self.sections = sections

        for title, sec_keys in sections:
            if all(k.startswith("column_index_") for k in sec_keys):
                frame = self._builder._build_column_index_frame(title, sec_keys)
                self.column_index_frames.append(frame)
            elif title == "" and self.general_frame is None:
                self.general_frame = self._builder.build_compact_frame(title, sec_keys)
            else:
                frame = self._builder._build_regular_section(title, sec_keys)
                self.section_widgets.append(frame)

        self._widest_section = max(
            (w.sizeHint().width() for w in self.section_widgets), default=1
        )
        return self._arrange_columns(1)

    def build_controls_row(self) -> QHBoxLayout | None:
        """Build top-area (general + column_index in scroll areas).
        Returns None if not in compact mode (no preview)."""
        if not self._has_preview:
            return None
        if not self.general_frame and not self.column_index_frames:
            return None

        controls_row = QHBoxLayout()
        controls_row.setSpacing(self._margin)

        if self.general_frame is not None:
            general_scroll = QScrollArea()
            general_scroll.setWidget(self.general_frame)
            general_scroll.setWidgetResizable(True)
            controls_row.addWidget(general_scroll)

        for frame in self.column_index_frames:
            col_scroll = QScrollArea()
            col_scroll.setWidget(frame)
            col_scroll.setWidgetResizable(True)
            controls_row.addWidget(col_scroll)

        return controls_row

    def reflow(self, viewport_width: int) -> QWidget | None:
        """Recalculate columns. Return new container if changed, else None."""
        if not self.section_widgets:
            return None
        new_num = min(5, max(1, viewport_width // max(self._widest_section, 1)))
        if new_num == self._num_columns:
            return None
        return self._arrange_columns(new_num)

    def reorder_sections(self) -> QWidget | None:
        """Reorder sections by column_index. Return new container."""
        if not self.section_widgets:
            return None

        frame_index = []
        for frame in self.section_widgets:
            keys = frame.property("section_keys")
            if not keys:
                continue
            min_idx = 999999
            for k in keys:
                if k.startswith("column_index_"):
                    val = self._current_values.get(k, 999999)
                    if isinstance(val, (int, float)):
                        min_idx = min(min_idx, val)
            frame_index.append((frame, min_idx))

        frame_index.sort(key=lambda x: x[1])
        self.section_widgets = [f for f, _ in frame_index]

        return self._arrange_columns(self._num_columns)

    def _arrange_columns(self, num_columns: int) -> QWidget:
        """Distribute section widgets into num_columns columns and return a container."""
        self._num_columns = num_columns
        total_rows = sum(
            (w.property("estimated_rows") or 10) for w in self.section_widgets
        )
        max_rows = max(24, -(-total_rows // num_columns))  # ceiling division

        for w in self.section_widgets:
            w.setParent(None)

        columns: list[list[QFrame]] = [[] for _ in range(num_columns)]
        col_rows = [0] * num_columns

        for widget in self.section_widgets:
            est = widget.property("estimated_rows") or 10
            for col in range(num_columns):
                if col_rows[col] + est <= max_rows:
                    columns[col].append(widget)
                    col_rows[col] += est
                    break
            else:
                min_col = min(range(num_columns), key=lambda i: col_rows[i])
                columns[min_col].append(widget)
                col_rows[min_col] += est

        col_gap = UIScaler.size(1) if num_columns > 1 else 0
        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(col_gap)
        main_layout.setContentsMargins(0, 0, 0, 0)

        for col_widgets in columns:
            if not col_widgets:
                continue
            col_layout = QVBoxLayout()
            col_layout.setSpacing(0)
            col_layout.setContentsMargins(0, 0, 0, 0)
            for w in col_widgets:
                col_layout.addWidget(w)
            col_layout.addStretch(1)
            col_container = QWidget()
            col_container.setLayout(col_layout)
            main_layout.addWidget(col_container, 1)

        container = QWidget()
        container.setLayout(main_layout)
        return container
