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
    QAbstractItemView,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from ..formatter import format_option_name
from ._common import BaseDialog, UIScaler


class DisplayOrder(BaseDialog):
    """Adjust display order for widget column or row"""

    def __init__(self, parent, user_orders: dict, default_orders: dict):
        super().__init__(parent)
        self.setWindowTitle("Display Order")

        self._parent = parent
        self.temp_orders = user_orders
        self.default_orders = default_orders

        # List
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setMinimumHeight(UIScaler.size(20))
        self.list_widget.setSpacing(1)
        self._populate_list(self.temp_orders)

        # Button
        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self._reset_order)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self._apply_order)

        button_close = QDialogButtonBox(QDialogButtonBox.Close)
        button_close.clicked.connect(self.reject)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(button_reset)
        bottom_layout.addStretch()
        bottom_layout.addWidget(button_apply)
        bottom_layout.addWidget(button_close)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(bottom_layout)
        main_layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(main_layout)

        # Calculate size based on content after populating
        # self._fit_to_content()

    def _apply_order(self):
        """Apply display order"""
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            key = item.data(Qt.UserRole)
            if key in self.temp_orders:
                self.temp_orders[key] = row + 1

        self._parent.update_column_index(self.temp_orders)
        self._parent.applying()

    def _populate_list(self, target_orders: dict):
        """Populate list"""
        self.list_widget.clear()

        for key in sorted(target_orders, key=lambda k: target_orders[k]):
            # Strip prefix, then format
            short_key = key.replace("column_index_", "")
            item = QListWidgetItem(format_option_name(short_key))
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip("Click & Drag to Reorder Display")
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)

    def _reset_order(self):
        """Reset display order"""
        self._populate_list(self.default_orders)
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
