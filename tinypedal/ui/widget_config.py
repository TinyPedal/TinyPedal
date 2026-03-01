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
Widget config dialog

This dialog is only used for widget configs (not modules/settings).
Own dialog — does not inherit from or reuse UserConfig.

Uses:
- widget_config_grouper.py: split widget keys into sections (general, show_* groups, column_index)
- display_order.py: popup dialog for column_index_* reordering

Layout:
    ┌─────────────────────────────────────────┐
    │ Search bar                              │
    ├─────────────────────────────────────────┤
    │ Options grid (scrollable)               │
    │ (all keys except column_index_*)        │
    ├─────────────────────────────────────────┤
    │ Reset  Display Order   Apply Save Cancel│
    └─────────────────────────────────────────┘

Follows same conventions as config.py:
- Same editor creation pattern (__add_option_bool, etc.)
- Same save/validate pattern (option dicts per type)
- Same button bar (QDialogButtonBox)
- Same singleton_dialog decorator
- Reuses set_preset_name, add_context_menu, context_menu_reset_option from config.py
"""


# --- Imports ----------------------------------------------------------------
# Same imports as config.py (lines 23-62), plus:
# from .widget_config_grouper import WidgetConfigGrouper
# from .display_order import DisplayOrderDialog


# --- Widget Config Dialog ---------------------------------------------------
# Same __init__ signature as UserConfig so module_view.py can call both the same way.

class WidgetConfig:
    """Widget configuration dialog."""

    def __init__(self, parent, key_name, cfg_type, user_setting,
                 default_setting, reload_func, option_width=9):
        # Same base setup as UserConfig.__init__ (config.py line 201-269):
        # - set_config_title
        # - store attributes (reloading, key_name, cfg_type, etc.)
        # - option dicts per type (option_bool, option_color, etc.)
        #
        # Use WidgetConfigGrouper to split keys:
        # - column_index_* keys -> stored for DisplayOrderDialog
        # - all other keys -> create_options into QGridLayout
        #
        # Layout (top to bottom):
        # - Search bar
        # - Scrollable options grid
        # - Button bar: Reset | Display Order | ... | Apply Save Cancel
        pass

    # --- Search -------------------------------------------------------------

    def _create_search_bar(self):
        # QLineEdit with placeholder "Search..."
        # Connected to _apply_filter on textChanged
        pass

    def _apply_filter(self, text):
        # Show/hide rows in the grid based on whether key matches search text
        # Match against key name (lowercase contains)
        pass

    # --- Display Order ------------------------------------------------------

    def _open_display_order(self):
        # Open DisplayOrderDialog with current column_index_* values
        # On close: read new order via get_order(), store updated values
        # Values written to user_setting on WidgetConfig save
        pass

    # --- Options (same pattern as UserConfig) --------------------------------
    # Reuse config.py functions: add_context_menu, context_menu_reset_option
    # Same __add_option_* methods as UserConfig (config.py lines 459-587)
    # Same create_options loop (config.py lines 401-448)

    def create_options(self, layout):
        # Same as UserConfig.create_options (config.py line 401)
        # BUT: skip keys that start with "column_index_"
        # Those are handled by DisplayOrderDialog
        pass

    # --- Save / Reset (same pattern as UserConfig) --------------------------

    def applying(self):
        # Same as UserConfig.applying (config.py line 271)
        pass

    def saving(self):
        # Same as UserConfig.saving (config.py line 276)
        pass

    def save_setting(self, is_apply):
        # Same as UserConfig.save_setting (config.py line 313)
        # Additional: write stored column_index_* values to user_setting
        pass

    def reset_setting(self):
        # Same as UserConfig.reset_setting (config.py line 279)
        # Additional: reset stored column_index_* values to defaults
        pass

    def value_error_message(self, value_type, option_name):
        # Same as UserConfig.value_error_message (config.py line 393)
        pass
