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
Build section frames for the configuration dialog.
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ...formatter import format_option_name
from .drag_drop_list import DragDropOrderList
from .option_editors import create_editor


class SectionBuilder:
    """
    Builds all section frames for a UserConfig dialog and keeps track of created widgets.
    """

    def __init__(self, parent_dialog, current_values, update_callback, option_width,
                 highlight_callback=None):
        """
        Parameters
        ----------
        parent_dialog : UserConfig
            The parent configuration dialog (needed for parent widget and defaults).
        current_values : dict
            Dictionary of current (cached) values for all keys.
        update_callback : callable(key, new_value)
            Called when an editor's value changes.
        option_width : int
            Fixed width for editor widgets (in pixels).
        highlight_callback : callable(column_key), optional
            Called when a section (via its column_index_* key) is clicked.
        """
        self.parent = parent_dialog
        self.current_values = current_values
        self.update_callback = update_callback
        self.option_width = option_width
        self.highlight_callback = highlight_callback

        # Widget references for filtering / resetting
        self.row_widgets = {}           # key -> row container widget
        self.row_labels = {}             # key -> QLabel widget
        self.section_title_widgets = []  # list of (title_label, list_of_keys)
        self.column_order_widgets = {}   # key -> DragDropOrderList
        self.editors = {}                 # key -> editor widget (all types)

        # Frames that will be built
        self.general_frame = None
        self.section_frames = []
        self.column_index_frames = []

    def build_section_frame(self, title, keys):
        """
        Build a section frame for the given keys.
        Delegates to specialized builders based on key type.
        """
        if all(key.startswith("column_index_") for key in keys):
            return self._build_column_index_frame(title, keys)
        else:
            return self._build_regular_section(title, keys)

    def build_compact_frame(self, title, keys):
        """
        Build a compact two‑column frame (used for the "general" section).
        """
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        row_offset = 0
        if title is not None:
            header_text = (
                format_option_name(self.parent.key_name) if title == ""
                else format_option_name(title)
            )
            title_label = QLabel(f"<b>{header_text}</b>")
            font = title_label.font()
            font.setPointSize(font.pointSize() + 1)
            title_label.setFont(font)
            title_label.setStyleSheet("""
                background-color: palette(dark);
                color: palette(bright-text);
                border-bottom: 2px solid palette(mid);
                padding: 4px;
            """)
            layout.addWidget(title_label, 0, 0, 1, 4)
            row_offset = 1
            self.section_title_widgets.append((title_label, keys))

        for idx, key in enumerate(keys):
            grid_row = idx // 2 + row_offset
            grid_col = (idx % 2) * 2  # 0 or 2

            row_widget = QWidget()
            bg = "palette(alternate-base)" if (idx // 2) % 2 == 0 else "palette(base)"
            row_widget.setStyleSheet(f"background-color: {bg};")
            row_widget.setProperty("_base_bg", bg)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(4, 1, 4, 1)
            row_layout.setSpacing(4)

            label = QLabel(format_option_name(key))
            row_layout.addWidget(label)

            # Determine choices for dropdowns if needed
            choices = self._get_choices_for_key(key)
            editor = create_editor(
                self.parent,
                key,
                self.current_values[key],
                self.parent.default_setting[self.parent.key_name][key],
                self.update_callback,
                choices=choices
            )
            editor.setFixedHeight(22)
            editor.setFixedWidth(self.option_width)
            row_layout.addWidget(editor)

            row_widget.setLayout(row_layout)
            layout.addWidget(row_widget, grid_row, grid_col, 1, 2)

            self.row_widgets[key] = row_widget
            self.row_labels[key] = label
            self.editors[key] = editor

        frame = QFrame()
        frame.setObjectName("sectionFrame")
        frame.setLayout(layout)
        # approximate number of rows for column balancing
        frame.setProperty("estimated_rows", len(keys) // 2 + (1 if title is not None else 0))
        return frame

    def _build_regular_section(self, title, keys):
        """
        Build a standard section with title bar and alternating rows (one column).
        """
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        row_offset = 0
        if title is not None:
            header_text = (
                format_option_name(self.parent.key_name) if title == ""
                else format_option_name(title)
            )
            title_label = QLabel(f"<b>{header_text}</b>")
            font = title_label.font()
            font.setPointSize(font.pointSize() + 1)
            title_label.setFont(font)
            title_label.setStyleSheet("""
                background-color: palette(dark);
                color: palette(bright-text);
                border-bottom: 2px solid palette(mid);
                padding: 4px;
            """)
            layout.addWidget(title_label, 0, 0, 1, 2)
            row_offset = 1
            self.section_title_widgets.append((title_label, keys))

        for idx, key in enumerate(keys):
            row = idx + row_offset

            row_widget = QWidget()
            bg = "palette(alternate-base)" if idx % 2 == 0 else "palette(base)"
            row_widget.setStyleSheet(f"background-color: {bg};")
            row_widget.setProperty("_base_bg", bg)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(4, 1, 4, 1)
            row_layout.setSpacing(4)

            label = QLabel(format_option_name(key))
            row_layout.addWidget(label)

            choices = self._get_choices_for_key(key)
            editor = create_editor(
                self.parent,
                key,
                self.current_values[key],
                self.parent.default_setting[self.parent.key_name][key],
                self.update_callback,
                choices=choices
            )
            editor.setFixedHeight(22)
            editor.setFixedWidth(self.option_width)
            row_layout.addWidget(editor)

            row_widget.setLayout(row_layout)
            layout.addWidget(row_widget, row, 0, 1, 2)

            self.row_widgets[key] = row_widget
            self.row_labels[key] = label
            self.editors[key] = editor

        frame = QFrame()
        frame.setObjectName("sectionFrame")
        frame.setLayout(layout)
        frame.setProperty("estimated_rows", len(keys) + (1 if title is not None else 0))
        # Bewaar de bijbehorende keys voor later herordenen
        frame.setProperty("section_keys", keys)
        return frame

    def _build_column_index_frame(self, title, keys):
        """
        Build a frame with a drag‑and‑drop list for column order settings.
        """
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        col_title_label = None
        if title is not None:
            header_text = (
                format_option_name(self.parent.key_name) if title == ""
                else "Sections"  # Gewijzigd: "Sections" i.p.v. "Display Order"
            )
            col_title_label = QLabel(f"<b>{header_text}</b>")
            font = col_title_label.font()
            font.setPointSize(font.pointSize() + 1)
            col_title_label.setFont(font)
            col_title_label.setStyleSheet("""
                background-color: palette(dark);
                color: palette(bright-text);
                border-bottom: 2px solid palette(mid);
                padding: 4px;
            """)
            layout.addWidget(col_title_label)

        # Sort keys according to current values (they store the order index)
        sorted_keys = sorted(
            keys,
            key=lambda k: self.current_values.get(k, 999)
        )
        items = [
            (key, format_option_name(key[len("column_index_"):]))
            for key in sorted_keys
        ]

        def on_reorder(new_order):
            for index, key in enumerate(new_order, start=1):
                self.update_callback(key, index)
            # Laat de parent weten dat de volgorde is gewijzigd, zodat frames herschikt worden
            if hasattr(self.parent, 'on_column_order_changed'):
                self.parent.on_column_order_changed()

        row_height = 22 + 4  # approximate editor height plus some margin
        list_widget = DragDropOrderList(
            items=items,
            on_reorder_callback=on_reorder,
            row_height=row_height,
            parent=self.parent
        )
        # Verbind het signaal voor sectie‑klik als er een callback is meegegeven
        if self.highlight_callback is not None:
            list_widget.sectionClicked.connect(self.highlight_callback)

        for key in keys:
            self.column_order_widgets[key] = list_widget
            # Note: we do not store a separate editor for these keys;
            # the order is managed by the list widget.

        layout.addWidget(list_widget)

        if col_title_label is not None:
            self.section_title_widgets.append((col_title_label, keys))

        frame = QFrame()
        frame.setObjectName("sectionFrame")
        frame.setLayout(layout)
        frame.setProperty("estimated_rows", len(keys) + (2 if title is not None else 1))
        return frame

    def _get_choices_for_key(self, key):
        """
        Return a list of choices for dropdowns, or None if not applicable.
        This method can be extended to fetch dynamic lists (e.g., heatmap names).
        """
        # Placeholder – in the future we could query the parent for a mapping.
        return None
