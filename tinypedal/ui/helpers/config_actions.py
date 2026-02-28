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
Stateless save/reset/validate functions for config dialog.
"""

import re
import time

from PySide2.QtWidgets import QCheckBox, QComboBox, QLineEdit, QMessageBox

from ... import regex_pattern as rxp
from ...const_file import ConfigType
from ...formatter import format_option_name
from ...setting import cfg
from ...userfile import set_relative_path, set_user_data_path
from ...validator import is_clock_format, is_hex_color, is_string_number


def save_setting(original_keys, current_values, user_setting, key_name,
                 cfg_type, editors, reload_func, parent) -> bool:
    """Validate and save all values. Returns True on success."""
    target = user_setting[key_name]
    error_found = False

    for key in original_keys:
        value = current_values[key]

        if re.search(rxp.CFG_BOOL, key):
            target[key] = value

        elif re.search(rxp.CFG_COLOR, key):
            if is_hex_color(value):
                target[key] = value
            else:
                _value_error(parent, "color", key)
                error_found = True

        elif re.search(rxp.CFG_USER_PATH, key):
            value = set_relative_path(value)
            if set_user_data_path(value):
                target[key] = value
                editor = editors.get(key)
                if editor:
                    editor.setText(value)
                    current_values[key] = value
            else:
                _value_error(parent, "path", key)
                error_found = True

        elif re.search(rxp.CFG_USER_IMAGE, key):
            target[key] = value

        elif re.search(rxp.CFG_FONT_NAME, key) or re.search(rxp.CFG_HEATMAP, key) or \
             any(re.search(ref, key) for ref in rxp.CHOICE_UNITS) or \
             any(re.search(ref, key) for ref in rxp.CHOICE_COMMON):
            target[key] = value

        elif re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
            if re.search(rxp.CFG_CLOCK_FORMAT, key) and not is_clock_format(value):
                _value_error(parent, "clock format", key)
                error_found = True
            else:
                target[key] = value

        elif re.search(rxp.CFG_INTEGER, key):
            str_val = str(value)
            if is_string_number(str_val):
                target[key] = int(str_val)
            else:
                _value_error(parent, "number", key)
                error_found = True

        else:  # float fallback
            str_val = str(value)
            if is_string_number(str_val):
                num_val = float(str_val)
                if num_val % 1 == 0:
                    num_val = int(num_val)
                target[key] = num_val
            else:
                _value_error(parent, "number", key)
                error_found = True

    for key in original_keys:
        if key.startswith("column_index_"):
            target[key] = current_values[key]

    if error_found:
        return False

    if cfg_type == ConfigType.CONFIG:
        cfg.update_path()
        cfg.save(0, cfg_type=ConfigType.CONFIG)
    else:
        cfg.save(0)

    while cfg.is_saving:
        time.sleep(0.01)

    reload_func()
    return True


def reset_setting(editors, current_values, default_setting, key_name,
                  column_order_widgets, parent) -> bool:
    """Reset all editors to defaults. Returns True if confirmed."""
    from .._common import BaseDialog

    msg_text = (
        f"Reset all <b>{format_option_name(key_name)}</b> options to default?<br><br>"
        "Changes are only saved after clicking Apply or Save Button."
    )
    if not parent.confirm_operation(title="Reset Options", message=msg_text):
        return False

    for key, editor in editors.items():
        default = editor.defaults
        if isinstance(editor, QCheckBox):
            editor.setChecked(default)
            current_values[key] = default
        elif isinstance(editor, QLineEdit):
            editor.setText(str(default))
            current_values[key] = default
        elif isinstance(editor, QComboBox):
            editor.setCurrentText(str(default))
            current_values[key] = default

    seen: set = set()
    for key, lw in column_order_widgets.items():
        if id(lw) not in seen:
            seen.add(id(lw))
            all_keys = [k for k, w in column_order_widgets.items() if w is lw]
            default_vals = {
                k: default_setting[key_name][k] for k in all_keys
            }
            lw.reset_to_defaults(default_vals)

    return True


def _value_error(parent, value_type: str, option_name: str):
    msg_text = (
        f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
        "<br><br>Changes are not saved."
    )
    QMessageBox.warning(parent, "Error", msg_text)
