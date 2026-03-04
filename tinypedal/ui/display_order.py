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
    QAbstractItemView
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
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setMinimumHeight(UIScaler.size(10))
        self._populate_list(self.options)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.list_widget)

        # Button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_order)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.update_order)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(reset_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(apply_btn)
        bottom_layout.addWidget(close_btn)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        main_layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(main_layout)

        # Calculate size based on content after populating
        # self._fit_to_content()

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
            # Strip prefix, then format
            short_key = key.replace("column_index_", "")
            item = QListWidgetItem(format_option_name(short_key))
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)

    def _reset_order(self):
        """Reset display order"""
        self._populate_list(self.default_values)
        self.list_widget.setCurrentRow(0)


    # def _fit_to_content(self):
    #     """Fit dialog size to content"""
    #     self.layout().activate()

    #     # Get width needed for longest item
    #     width = 0
    #     for row in range(self.list_widget.count()):
    #         item = self.list_widget.item(row)
    #         item_width = self.list_widget.fontMetrics().horizontalAdvance(item.text())
    #         width = max(width, item_width)

    #     # Add scrollbar width if needed, plus margins
    #     scrollbar_width = self.style().pixelMetric(self.style().PM_ScrollBarExtent)
    #     margins = self.layout().contentsMargins()

    #     total_width = (width + scrollbar_width + margins.left() + margins.right() +
    #                 UIScaler.size(6))

    #     # Height based on item count (with max limit)
    #     item_height = self.list_widget.sizeHintForRow(0)
    #     max_visible_items = 15  # Limit height for long lists
    #     visible_items = min(self.list_widget.count(), max_visible_items)

    #     total_height = (item_height * visible_items + margins.top() + margins.bottom() +
    #                     UIScaler.size(10))  # button row

    #     self.resize(total_width, total_height)
    #     self.setMinimumSize(total_width, total_height)
