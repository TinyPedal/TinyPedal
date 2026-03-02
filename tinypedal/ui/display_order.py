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
Display order dialog

Small popup dialog for reordering column_index_* settings.
Opened from WidgetConfig via "Display Order" button.
Sized to fit all items — no scrollbar needed.
"""

from __future__ import annotations

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from ..formatter import format_option_name
from ._common import BaseDialog, UIScaler


class DisplayOrderDialog(BaseDialog):
    """Popup dialog to reorder column_index_* settings.

    Uses QListWidget with up/down buttons.
    Window sized to show all items without scrollbar.
    """

    def __init__(self, parent, column_keys, current_values, default_values):
        """
        Args:
            parent: WidgetConfig instance.
            column_keys: list of "column_index_*" keys.
            current_values: dict key -> current int value.
            default_values: dict key -> default int value.
        """
        super().__init__(parent)
        self.setWindowTitle("Display Order")

        self.column_keys = column_keys
        self.current_values = current_values
        self.default_values = default_values

        # ---------- List widget ----------
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self._populate_list()

        # Fix height to avoid scrollbar
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_height = self.list_widget.sizeHintForRow(0)
        total_height = row_height * self.list_widget.count() + 2 * self.list_widget.frameWidth()
        self.list_widget.setFixedHeight(total_height)

        # ---------- Up/Down buttons ----------
        self.up_btn = QPushButton("▲")
        self.up_btn.setFixedWidth(UIScaler.size(4))
        self.up_btn.clicked.connect(self._move_up)

        self.down_btn = QPushButton("▼")
        self.down_btn.setFixedWidth(UIScaler.size(4))
        self.down_btn.clicked.connect(self._move_down)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.up_btn)
        button_layout.addWidget(self.down_btn)
        button_layout.addStretch()

        # ---------- Top area (list + buttons) ----------
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.list_widget)
        top_layout.addLayout(button_layout)

        # ---------- Bottom buttons ----------
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_order)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.accept)   # close with accepted

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)   # close with rejected

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.reset_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.apply_btn)
        bottom_layout.addWidget(self.close_btn)

        # ---------- Main layout ----------
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        main_layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(main_layout)

        # Size dialog to fit content exactly (no resizing)
        self.adjustSize()
        self.setFixedSize(self.size())

    # ------------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------------
    def _populate_list(self):
        """Fill list with keys sorted by current index."""
        sorted_keys = sorted(self.column_keys, key=lambda k: self.current_values[k])
        for key in sorted_keys:
            display_name = format_option_name(key)
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)

    # ------------------------------------------------------------------------
    # Slot methods
    # ------------------------------------------------------------------------
    def _move_up(self):
        """Move selected item one position up."""
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        """Move selected item one position down."""
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def _reset_order(self):
        """Restore default order (based on default_values)."""
        self.list_widget.clear()
        sorted_keys = sorted(self.column_keys, key=lambda k: self.default_values[k])
        for key in sorted_keys:
            display_name = format_option_name(key)
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)
        # Optionally select first item
        self.list_widget.setCurrentRow(0)

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------
    def get_order(self) -> dict:
        """Return dictionary mapping each key to its new 1‑based index."""
        order = {}
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            key = item.data(Qt.UserRole)
            order[key] = row + 1   # 1‑based index
        return order
