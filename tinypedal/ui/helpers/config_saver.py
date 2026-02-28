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

"""Validation and save logic for config dialog"""

import re
import time

from ... import regex_pattern as rxp
from ...const_file import ConfigType
from ...setting import cfg
from ...userfile import set_relative_path, set_user_data_path
from ...validator import is_clock_format, is_hex_color, is_string_number


def validate_and_save(keys, current_values, target, editors, cfg_type, reload_func, error_callback):
    """Validate all values and save to config

    Parameters
    ----------
    keys : list of str
        Original keys in order.
    current_values : dict
        Current values from editors.
    target : dict
        The target user setting dictionary to update.
    editors : dict
        Mapping key -> editor widget (for updating path editor).
    cfg_type : ConfigType
        Type of configuration being edited.
    reload_func : callable
        Function to reload the config after save.
    error_callback : callable
        Function taking (value_type, option_name) to display error.

    Returns
    -------
    bool
        True if save succeeded, False if validation failed.
    """
    error_found = False

    for key in keys:
        value = current_values[key]

        # Boolean
        if re.search(rxp.CFG_BOOL, key):
            target[key] = value

        # Color
        elif re.search(rxp.CFG_COLOR, key):
            if is_hex_color(value):
                target[key] = value
            else:
                error_callback("color", key)
                error_found = True

        # Path
        elif re.search(rxp.CFG_USER_PATH, key):
            value = set_relative_path(value)
            if set_user_data_path(value):
                target[key] = value
                editor = editors.get(key)
                if editor:
                    editor.setText(value)
                    current_values[key] = value
            else:
                error_callback("path", key)
                error_found = True

        # Image
        elif re.search(rxp.CFG_USER_IMAGE, key):
            target[key] = value

        # Combo choices
        elif (re.search(rxp.CFG_FONT_NAME, key) or
              re.search(rxp.CFG_HEATMAP, key) or
              any(re.search(ref, key) for ref in rxp.CHOICE_UNITS) or
              any(re.search(ref, key) for ref in rxp.CHOICE_COMMON)):
            target[key] = value

        # Clock format / string
        elif re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
            if re.search(rxp.CFG_CLOCK_FORMAT, key) and not is_clock_format(value):
                error_callback("clock format", key)
                error_found = True
            else:
                target[key] = value

        # Integer
        elif re.search(rxp.CFG_INTEGER, key):
            str_val = str(value)
            if is_string_number(str_val):
                target[key] = int(str_val)
            else:
                error_callback("number", key)
                error_found = True

        # Float fallback
        else:
            str_val = str(value)
            if is_string_number(str_val):
                num_val = float(str_val)
                if num_val % 1 == 0:
                    num_val = int(num_val)
                target[key] = num_val
            else:
                error_callback("number", key)
                error_found = True

    # Ensure column indexes are saved (they were already handled above,
    # but this loop guarantees they are written even if they didn't match any pattern)
    for key in keys:
        if key.startswith("column_index_"):
            target[key] = current_values[key]

    if error_found:
        return False

    # Save to disk
    if cfg_type == ConfigType.CONFIG:
        cfg.update_path()
        cfg.save(0, cfg_type=ConfigType.CONFIG)
    else:
        cfg.save(0)
    while cfg.is_saving:
        time.sleep(0.01)
    reload_func()
    return True
