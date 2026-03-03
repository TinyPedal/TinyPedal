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
    """Display order dialog"""

    def __init__(self, parent, options: dict, default_values: dict):
        super().__init__(parent)
        self.setWindowTitle("Display Order")

        self._parent = parent
        self.options = options
        self.default_values = default_values
        self.column_keys = [k for k in options if k.startswith("column_index_")]

        # List
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self._populate_list(self.options)

        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_height = self.list_widget.sizeHintForRow(0)
        total_height = row_height * self.list_widget.count() + 2 * self.list_widget.frameWidth()
        self.list_widget.setFixedHeight(total_height)

        # Up/Down button
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

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.list_widget)
        top_layout.addLayout(button_layout)

        # Button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_order)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.update_order)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.reset_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.apply_btn)
        bottom_layout.addWidget(self.close_btn)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        main_layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(main_layout)

        self.adjustSize()
        self.setFixedSize(self.size())

    def update_order(self):
        """Update display order"""
        new_order = self.get_order()
        for key, index in new_order.items():
            self.options[key] = index
        self._parent.update_column_index()
        self._parent.applying()

    def get_order(self) -> dict:
        """Get display order"""
        order = {}
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            key = item.data(Qt.UserRole)
            order[key] = row + 1
        return order

    def _populate_list(self, values: dict):
        """Populate list"""
        self.list_widget.clear()
        for key in sorted(self.column_keys, key=lambda k: values[k]):
            item = QListWidgetItem(format_option_name(key))
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)

    def _reset_order(self):
        """Reset display order"""
        self._populate_list(self.default_values)
        self.list_widget.setCurrentRow(0)

    def _move_up(self):
        """Move selected item up"""
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        """Move selected item down"""
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)
