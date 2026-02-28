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
Editor widgets and context menu for configuration options.
"""

import os
import re

from PySide2.QtCore import QPoint, Qt
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QMenu,
    QWidget,
)

from .. import regex_pattern as rxp
from ._common import (
    DoubleClickEdit,
    QVAL_COLOR,
    QVAL_FLOAT,
    QVAL_INTEGER,
)


# ----------------------------------------------------------------------
# Font list helper
# ----------------------------------------------------------------------
def get_font_list() -> list[str]:
    """Get all available font families list"""
    if os.getenv("PYSIDE_OVERRIDE") == "6":  # no instance in qt6
        return QFontDatabase.families()  # type: ignore[call-arg]
    return QFontDatabase().families()


# ----------------------------------------------------------------------
# Context menu for reset
# ----------------------------------------------------------------------
def add_context_menu(parent: QWidget):
    """Add context menu to parent widget for resetting to default."""
    parent.setContextMenuPolicy(Qt.CustomContextMenu)
    parent.customContextMenuRequested.connect(
        lambda pos, p=parent: _context_menu_reset_option(pos, p)
    )


def _context_menu_reset_option(position: QPoint, parent):
    """Show context menu with reset action."""
    menu = QMenu()  # temporary menu, no parent
    reset_action = menu.addAction("Reset to Default")
    action = menu.exec_(parent.mapToGlobal(position))
    if action == reset_action:
        if isinstance(parent, QCheckBox):
            parent.setChecked(parent.defaults)
        elif isinstance(parent, QLineEdit):
            parent.setText(str(parent.defaults))
        elif isinstance(parent, QComboBox):
            parent.setCurrentText(str(parent.defaults))


# ----------------------------------------------------------------------
# Editor factory
# ----------------------------------------------------------------------
def create_editor(
    parent,
    key: str,
    current_val,
    default_val,
    update_callback,
    *,
    choices: list[str] | None = None,
):
    """
    Create the appropriate editor widget for the given key.

    Parameters
    ----------
    parent : QWidget
        Parent widget.
    key : str
        Configuration key.
    current_val : any
        Current value from cache.
    default_val : any
        Default value from defaults.
    update_callback : callable(key, new_value)
        Called when the editor value changes.
    choices : list of str, optional
        List of choices for combo boxes (used for units/common/heatmap).

    Returns
    -------
    QWidget
        The editor widget.
    """
    # Boolean (checkbox)
    if re.search(rxp.CFG_BOOL, key):
        editor = QCheckBox(parent)
        editor.setChecked(bool(current_val))
        editor.stateChanged.connect(
            lambda state, k=key: update_callback(k, bool(state))
        )

    # Color string (with preview)
    elif re.search(rxp.CFG_COLOR, key):
        editor = DoubleClickEdit(parent, mode="color", init=current_val)
        editor.setValidator(QVAL_COLOR)
        editor.textChanged.connect(editor.preview_color)
        editor.setText(str(current_val))
        editor.textChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # User path string (directory)
    elif re.search(rxp.CFG_USER_PATH, key):
        editor = DoubleClickEdit(parent, mode="path", init=current_val)
        editor.setText(str(current_val))
        editor.textChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # User image file path
    elif re.search(rxp.CFG_USER_IMAGE, key):
        editor = DoubleClickEdit(parent, mode="image", init=current_val)
        editor.setText(str(current_val))
        editor.textChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Font name (combo box)
    elif re.search(rxp.CFG_FONT_NAME, key):
        editor = QComboBox(parent)
        editor.addItems(get_font_list())
        editor.setCurrentText(str(current_val))
        editor.currentTextChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Heatmap selection (combo box using provided choices)
    elif re.search(rxp.CFG_HEATMAP, key):
        editor = QComboBox(parent)
        if choices:
            editor.addItems(choices)
        editor.setCurrentText(str(current_val))
        editor.currentTextChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Units choice (combo box using provided choices)
    elif any(re.search(ref, key) for ref in rxp.CHOICE_UNITS):
        editor = QComboBox(parent)
        if choices:
            editor.addItems(choices)
        else:
            # fallback: try to get from CHOICE_UNITS based on matching ref
            for ref, items in rxp.CHOICE_UNITS.items():
                if re.search(ref, key):
                    editor.addItems(items)
                    break
        editor.setCurrentText(str(current_val))
        editor.currentTextChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Common choice (combo box using provided choices)
    elif any(re.search(ref, key) for ref in rxp.CHOICE_COMMON):
        editor = QComboBox(parent)
        if choices:
            editor.addItems(choices)
        else:
            for ref, items in rxp.CHOICE_COMMON.items():
                if re.search(ref, key):
                    editor.addItems(items)
                    break
        editor.setCurrentText(str(current_val))
        editor.currentTextChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Clock format string (free text)
    elif re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
        editor = QLineEdit(parent)
        editor.setText(str(current_val))
        editor.textChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Integer (validated line edit)
    elif re.search(rxp.CFG_INTEGER, key):
        editor = QLineEdit(parent)
        editor.setValidator(QVAL_INTEGER)
        editor.setText(str(current_val))
        editor.textChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Float (validated line edit)
    else:
        # fallback to float validator
        editor = QLineEdit(parent)
        editor.setValidator(QVAL_FLOAT)
        editor.setText(str(current_val))
        editor.textChanged.connect(
            lambda text, k=key: update_callback(k, text)
        )

    # Store default value and add context menu
    editor.defaults = default_val
    add_context_menu(editor)

    return editor
