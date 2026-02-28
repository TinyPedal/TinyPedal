"""Option editor factory functions"""

import os
import re
from functools import partial

from PySide2.QtCore import QPoint, Qt
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QCheckBox, QComboBox, QLineEdit, QMenu, QWidget

from ... import regex_pattern as rxp
from .._common import DoubleClickEdit, QVAL_COLOR, QVAL_FLOAT, QVAL_INTEGER


def get_font_list():
    if os.getenv("PYSIDE_OVERRIDE") == "6":
        return QFontDatabase.families()
    return QFontDatabase().families()


def add_context_menu(parent):
    parent.setContextMenuPolicy(Qt.CustomContextMenu)
    parent.customContextMenuRequested.connect(
        lambda pos, p=parent: _context_menu_reset(pos, p)
    )


def _context_menu_reset(position, parent):
    menu = QMenu()
    reset_action = menu.addAction("Reset to Default")
    action = menu.exec_(parent.mapToGlobal(position))
    if action == reset_action:
        if isinstance(parent, QCheckBox):
            parent.setChecked(parent.defaults)
        elif isinstance(parent, QLineEdit):
            parent.setText(str(parent.defaults))
        elif isinstance(parent, QComboBox):
            parent.setCurrentText(str(parent.defaults))


# Editor factory functions

def _create_checkbox(parent, key, current_val, default_val, update_cb, choices):
    editor = QCheckBox(parent)
    editor.setChecked(bool(current_val))
    editor.stateChanged.connect(lambda state: update_cb(key, bool(state)))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_color_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = DoubleClickEdit(parent, mode="color", init=current_val)
    editor.setValidator(QVAL_COLOR)
    editor.textChanged.connect(editor.preview_color)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_path_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = DoubleClickEdit(parent, mode="path", init=current_val)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_image_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = DoubleClickEdit(parent, mode="image", init=current_val)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_font_combo(parent, key, current_val, default_val, update_cb, choices):
    editor = QComboBox(parent)
    editor.addItems(get_font_list())
    editor.setCurrentText(str(current_val))
    editor.currentTextChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_heatmap_combo(parent, key, current_val, default_val, update_cb, choices):
    editor = QComboBox(parent)
    if choices:
        editor.addItems(choices)
    editor.setCurrentText(str(current_val))
    editor.currentTextChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_units_combo(parent, key, current_val, default_val, update_cb, choices):
    editor = QComboBox(parent)
    if choices:
        editor.addItems(choices)
    else:
        for ref, items in rxp.CHOICE_UNITS.items():
            if re.search(ref, key):
                editor.addItems(items)
                break
    editor.setCurrentText(str(current_val))
    editor.currentTextChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_common_combo(parent, key, current_val, default_val, update_cb, choices):
    editor = QComboBox(parent)
    if choices:
        editor.addItems(choices)
    else:
        for ref, items in rxp.CHOICE_COMMON.items():
            if re.search(ref, key):
                editor.addItems(items)
                break
    editor.setCurrentText(str(current_val))
    editor.currentTextChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_string_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = QLineEdit(parent)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_integer_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = QLineEdit(parent)
    editor.setValidator(QVAL_INTEGER)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


def _create_float_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = QLineEdit(parent)
    editor.setValidator(QVAL_FLOAT)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    add_context_menu(editor)
    return editor


# Dispatch table
_EDITOR_DISPATCH = [
    (rxp.CFG_BOOL, _create_checkbox),
    (rxp.CFG_COLOR, _create_color_editor),
    (rxp.CFG_USER_PATH, _create_path_editor),
    (rxp.CFG_USER_IMAGE, _create_image_editor),
    (rxp.CFG_FONT_NAME, _create_font_combo),
    (rxp.CFG_HEATMAP, _create_heatmap_combo),
]

# Add unit and common choice patterns
for _ref in rxp.CHOICE_UNITS:
    _EDITOR_DISPATCH.append((_ref, _create_units_combo))
for _ref in rxp.CHOICE_COMMON:
    _EDITOR_DISPATCH.append((_ref, _create_common_combo))

_EDITOR_DISPATCH.extend([
    (rxp.CFG_CLOCK_FORMAT, _create_string_editor),
    (rxp.CFG_STRING, _create_string_editor),
    (rxp.CFG_INTEGER, _create_integer_editor),
])


def create_editor(parent, key, current_val, default_val, update_cb, *, choices=None):
    """Create appropriate editor widget based on key pattern"""
    for pattern, factory in _EDITOR_DISPATCH:
        if re.search(pattern, key):
            return factory(parent, key, current_val, default_val, update_cb, choices)
    return _create_float_editor(parent, key, current_val, default_val, update_cb, choices)
