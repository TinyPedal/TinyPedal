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

Layout:
    ┌──────────────────────┐
    │ Column 1        ▲ ▼  │
    │ Column 2             │
    │ Column 3             │
    │ ...                  │
    ├──────────────────────┤
    │ Reset     Apply Close│
    └──────────────────────┘
"""


class DisplayOrderDialog:
    """Popup dialog to reorder column_index_* settings.

    Uses QListWidget with up/down buttons.
    Window sized to show all items without scrollbar.
    """

    def __init__(self, parent, column_keys, current_values, default_values):
        # parent: WidgetConfig instance
        # column_keys: list of "column_index_*" keys
        # current_values: dict key -> current int value
        # default_values: dict key -> default int value
        #
        # Build: QListWidget sorted by current value
        # Each item: display name + key stored in Qt.UserRole
        # Up/Down buttons to the right of the list
        # Reset/Apply/Close buttons at the bottom
        # Size window to fit all items (no scrollbar)
        pass

    def _move_up(self):
        # Swap selected item with item above
        # Update numbering
        pass

    def _move_down(self):
        # Swap selected item with item below
        # Update numbering
        pass

    def _reset_order(self):
        # Sort items by default_values order
        pass

    def get_order(self):
        # Return dict: key -> new index (1-based)
        # Called by WidgetConfig after dialog closes
        pass
