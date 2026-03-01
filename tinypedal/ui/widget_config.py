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

"""Widget config dialog"""

from __future__ import annotations

import copy
import importlib
import logging
import os
import re
import time
from functools import partial

from PySide2.QtCore import QMimeData, QTimer, Qt, Signal
from PySide2.QtGui import QDrag, QFontDatabase, QKeySequence, QPixmap, QShortcut
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import regex_pattern as rxp
from ..const_file import ConfigType
from ..formatter import format_option_name
from ..setting import cfg
from ..userfile import set_relative_path, set_user_data_path
from ..validator import is_clock_format, is_hex_color, is_string_number
from ._common import (
    BaseDialog,
    DoubleClickEdit,
    QVAL_COLOR,
    QVAL_FLOAT,
    QVAL_INTEGER,
    UIScaler,
    singleton_dialog,
)

logger = logging.getLogger(__name__)

ROW_HEIGHT = UIScaler.size(3)


# ---- Private helper classes ------------------------------------------------

class _ColumnsRow(QWidget):
    """Dynamic grid that reflows columns on resize"""

    def __init__(self, widgets=None, max_columns=5, spacing=0, parent=None):
        super().__init__(parent)
        self._max_columns = max_columns
        self._widgets = []
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(spacing)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._reflow)
        if widgets:
            self.setWidgets(widgets)

    def setWidgets(self, widgets):
        """Replace child widgets (not deleted, ownership stays with caller)"""
        self._clear_layout()
        self._widgets = list(widgets)
        self._reflow()

    def _reflow(self):
        alive = []
        for w in self._widgets:
            try:
                w.sizeHint()
                alive.append(w)
            except RuntimeError:
                pass
        self._widgets = alive
        if not self._widgets:
            self.updateGeometry()
            return
        avail_width = self.width()
        if avail_width <= 0:
            parent = self.parent()
            avail_width = parent.width() if parent else 800
        widest = max((w.sizeHint().width() for w in self._widgets), default=1)
        num_cols = max(1, min(self._max_columns, avail_width // max(widest, 1)))
        self._clear_layout()
        for idx, w in enumerate(self._widgets):
            self._grid.addWidget(w, idx // num_cols, idx % num_cols, Qt.AlignTop)
            w.show()
        self.updateGeometry()

    def _clear_layout(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(50)


class _OptionTable(QWidget):
    """Table with label-editor rows and optional title"""

    def __init__(self, parent=None, columns=1, row_height=24, editor_width=0,
                 padding=(4, 1, 4, 1), label_alignment=Qt.AlignLeft | Qt.AlignVCenter):
        super().__init__(parent)
        self._columns = columns
        self._row_height = row_height
        self._editor_width = editor_width
        self._padding = padding
        self._label_alignment = label_alignment
        self._keys = []
        self._row_widgets = {}
        self._row_labels = {}
        self._title_label = None
        self._extra_rows = 0
        self._section_headers = []
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._layout = QGridLayout(self)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def set_title(self, title):
        if self._title_label is None:
            self._title_label = QLabel(f"<b>{title}</b>")
            self._title_label.setObjectName("sectionTitle")
            font = self._title_label.font()
            font.setPointSize(font.pointSize() + 1)
            self._title_label.setFont(font)
            self._layout.addWidget(self._title_label, 0, 0, 1, self._columns * 2)
        else:
            self._title_label.setText(f"<b>{title}</b>")

    def add_section_header(self, title):
        """Add a section sub-header spanning all columns"""
        row_index = len(self._keys) + self._extra_rows
        if self._title_label is not None:
            row_index += self._columns
        grid_row = row_index // self._columns
        label = QLabel(f"<b>{title}</b>")
        label.setObjectName("sectionTitle")
        font = label.font()
        font.setPointSize(font.pointSize() + 1)
        label.setFont(font)
        self._layout.addWidget(label, grid_row, 0, 1, self._columns * 2)
        self._section_headers.append(label)
        self._extra_rows += self._columns

    def add_row(self, key, label_text, editor):
        """Add a label-editor row"""
        row_index = len(self._keys) + self._extra_rows
        if self._title_label is not None:
            row_index += self._columns
        col_offset = (row_index % self._columns) * 2
        grid_row = row_index // self._columns
        row_widget = QWidget()
        row_widget.setFixedHeight(self._row_height)
        bg = "palette(alternate-base)" if (grid_row % 2 == 0) else "palette(base)"
        row_widget.setStyleSheet(f"background-color: {bg};")
        row_widget.setProperty("_base_bg", bg)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(*self._padding)
        row_layout.setSpacing(self._padding[0])
        label = QLabel(label_text)
        label.setAlignment(self._label_alignment)
        label.setCursor(Qt.PointingHandCursor)
        row_layout.addWidget(label, 1)
        if self._editor_width:
            editor.setFixedWidth(self._editor_width)
        row_layout.addWidget(editor, 0, Qt.AlignRight | Qt.AlignVCenter)
        self._layout.addWidget(row_widget, grid_row, col_offset, 1, 2)
        self._keys.append(key)
        self._row_widgets[key] = row_widget
        self._row_labels[key] = label

    def row_widget(self, key):
        return self._row_widgets.get(key)

    def row_label(self, key):
        return self._row_labels.get(key)

    def keys(self):
        return self._keys[:]

    @property
    def title_label(self):
        return self._title_label


class _ClickableLabel(QLabel):
    """Label that emits clicked on left mouse press"""
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _DragHandle(QLabel):
    """Drag handle for reordering rows"""

    def __init__(self, text=" \u22ee\u22ee ", width=20, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(width)
        self.setCursor(Qt.OpenHandCursor)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec_(Qt.MoveAction)


class _OrderRow(QWidget):
    """Row with number, label, and drag handle"""
    clicked = Signal()

    def __init__(self, key, label, row_height, parent=None):
        super().__init__(parent)
        self.key = key
        self.label_text = label
        self.setFixedHeight(row_height)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.number_label = _ClickableLabel()
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setFixedWidth(row_height)
        self.number_label.setCursor(Qt.PointingHandCursor)
        self.number_label.clicked.connect(self.clicked)
        self.text_label = _ClickableLabel(label)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setIndent(5)
        self.text_label.setFixedHeight(row_height)
        self.text_label.setCursor(Qt.PointingHandCursor)
        self.text_label.clicked.connect(self.clicked)
        self.drag_handle = _DragHandle(parent=self)
        layout.addWidget(self.number_label)
        layout.addWidget(self.text_label, 1)
        layout.addWidget(self.drag_handle)

    def set_number(self, number):
        self.number_label.setText(str(number))

    def set_base_bg(self, bg):
        self._base_bg = bg
        self.setStyleSheet(f"background-color: {bg};")

    def set_dimmed(self, dimmed):
        if dimmed:
            self.setStyleSheet("background-color: palette(window);")
            self.number_label.setStyleSheet("color: palette(mid);")
            self.text_label.setStyleSheet("color: palette(mid);")
        else:
            bg = getattr(self, "_base_bg", "palette(base)")
            self.setStyleSheet(f"background-color: {bg};")
            self.number_label.setStyleSheet("")
            self.text_label.setStyleSheet("")


class _DragDropOrderList(QWidget):
    """Reorderable list with drag-and-drop"""

    itemClicked = Signal(str)
    orderChanged = Signal(list)

    def __init__(self, items, row_height=24, parent=None):
        super().__init__(parent)
        self._row_height = row_height
        self._original_items = items[:]
        self._items = items[:]
        self._filter_text = ""
        self._title_widget = None
        self.setAcceptDrops(True)
        self._drop_indicator = QFrame()
        self._drop_indicator.setFixedHeight(2)
        self._drop_indicator.hide()
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._rebuild_rows()

    def set_title(self, title):
        """Add a styled header above the list"""
        if self._title_widget:
            self._title_widget.deleteLater()
        header = QLabel(f"<b>{title}</b>")
        header.setObjectName("sectionTitle")
        font = header.font()
        font.setPointSize(font.pointSize() + 1)
        header.setFont(font)
        self._layout.insertWidget(0, header)
        self._title_widget = header

    def _rebuild_rows(self):
        title = self._title_widget
        if title:
            self._layout.removeWidget(title)
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if title:
            self._layout.addWidget(title)
        for key, label in self._items:
            row = _OrderRow(key, label, self._row_height, self)
            row.clicked.connect(lambda k=key: self.itemClicked.emit(k))
            self._layout.addWidget(row)
        self._update_row_numbers()
        self._update_row_colors()
        self._apply_filter_to_rows()

    def _update_row_numbers(self):
        for i, row in enumerate(self._rows()):
            row.set_number(i + 1)

    def _update_row_colors(self):
        for i, row in enumerate(self._rows()):
            bg = "palette(alternate-base)" if i % 2 == 0 else "palette(base)"
            row.set_base_bg(bg)

    def _rows(self):
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if isinstance(w, _OrderRow):
                yield w

    def dragEnterEvent(self, event):
        if isinstance(event.source(), _DragHandle):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not isinstance(event.source(), _DragHandle):
            event.ignore()
            return
        self._hide_indicator()
        insert_index = self._find_insert_index(event.pos())
        self._layout.insertWidget(insert_index, self._drop_indicator)
        self._drop_indicator.show()
        event.accept()

    def dragLeaveEvent(self, event):
        self._hide_indicator()
        event.accept()

    def dropEvent(self, event):
        source_handle = event.source()
        if not isinstance(source_handle, _DragHandle):
            return
        source_row = source_handle.parent()
        if not isinstance(source_row, _OrderRow):
            return
        self._hide_indicator()
        self._layout.removeWidget(source_row)
        insert_index = self._find_insert_index(event.pos())
        self._layout.insertWidget(insert_index, source_row)
        event.accept()
        self._update_model_from_layout()
        self._update_row_numbers()
        self._update_row_colors()
        self.orderChanged.emit([row.key for row in self._rows()])

    def _find_insert_index(self, pos):
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w and w.isVisible() and pos.y() < w.y() + w.height() // 2:
                return i
        return self._layout.count()

    def _hide_indicator(self):
        if self._drop_indicator.parent() == self:
            self._layout.removeWidget(self._drop_indicator)
            self._drop_indicator.hide()

    def _update_model_from_layout(self):
        self._items = [(row.key, row.label_text) for row in self._rows()]

    def apply_filter(self, text):
        """Apply filter text to dim non-matching rows"""
        self._filter_text = text
        self._apply_filter_to_rows()

    def _apply_filter_to_rows(self):
        for row in self._rows():
            matches = not self._filter_text or self._filter_text in row.key.lower()
            row.set_dimmed(not matches)

    def reset_to_defaults(self, default_order):
        """Reset list to default order"""
        self._items = sorted(
            self._original_items,
            key=lambda item: default_order.get(item[0], 999)
        )
        self._rebuild_rows()
        self.orderChanged.emit([key for key, _ in self._items])

    def keys(self):
        return [row.key for row in self._rows()]


class _WidgetPreview(QWidget):
    """Live preview of the widget being configured"""

    _DEBOUNCE_MS = 500

    def __init__(self, key_name, parent=None):
        super().__init__(parent)
        self._key_name = key_name
        self._active_widget = None
        self._pending_values = {}
        self._element_map = {}
        self._last_applied_values = {}
        self._module = self._load_module(key_name)
        self._available = self._module is not None
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._rebuild)
        self._setup_ui()
        if self._available:
            self._rebuild()

    @property
    def available(self):
        return self._available

    def _load_module(self, key_name):
        try:
            return importlib.import_module(f"tinypedal.widget.{key_name}")
        except ImportError:
            logger.debug("No preview for %s (module not found)", key_name)
            return None

    def _setup_ui(self):
        title = QLabel("<b>Preview</b>")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignCenter)
        self._inner_widget = QWidget()
        self._inner_layout = QVBoxLayout(self._inner_widget)
        self._inner_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self._inner_layout.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea()
        scroll.setWidget(self._inner_widget)
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        layout.addWidget(scroll)

    def schedule_refresh(self, current_values):
        """Schedule preview refresh, fast-path for show_* changes only"""
        self._pending_values = current_values.copy()
        if not self._active_widget or not self._element_map or not self._last_applied_values:
            self._debounce_timer.start(self._DEBOUNCE_MS)
            return
        changed_keys = {
            k for k, v in current_values.items()
            if self._last_applied_values.get(k) != v
        }
        if not changed_keys:
            return
        if all(k in self._element_map for k in changed_keys):
            self._apply_show_hide(current_values)
            self._last_applied_values = current_values.copy()
        else:
            self._debounce_timer.start(self._DEBOUNCE_MS)

    def cleanup(self):
        """Stop timers and remove active widget"""
        self._debounce_timer.stop()
        self._remove_active_widget()

    def _remove_active_widget(self):
        if self._active_widget is None:
            return
        if hasattr(self._active_widget, "_update_timer"):
            self._active_widget._update_timer.stop()
        self._active_widget.hide()
        self._inner_layout.removeWidget(self._active_widget)
        self._active_widget.deleteLater()
        self._active_widget = None
        self._element_map.clear()
        self._last_applied_values.clear()

    def _create_widget_instance(self, config):
        try:
            return self._module.Realtime(cfg, self._key_name)
        except Exception:
            logger.error("Preview creation failed for %s", self._key_name, exc_info=True)
            return None

    def _prepare_widget(self, widget, config):
        """Set up widget for embedded preview display"""
        widget.setParent(self._inner_widget)
        widget.setWindowFlags(Qt.Widget)
        widget.setAttribute(Qt.WA_TranslucentBackground, False)
        widget.move(0, 0)
        if hasattr(widget, "_update_timer") and hasattr(widget, "_update_interval"):
            widget._update_timer.start(widget._update_interval, widget)
        try:
            widget.timerEvent(None)
        except Exception:
            logger.debug("timerEvent failed in preview for %s", self._key_name, exc_info=True)

    def _rebuild(self):
        """Rebuild preview with current pending values"""
        self._remove_active_widget()
        if not self._available:
            return
        original = cfg.user.setting.get(self._key_name, {})
        patched = self._patch_config(original, self._pending_values)
        forced_show, patched = self._force_show_settings(patched)
        cfg.user.setting[self._key_name] = patched
        try:
            widget = self._create_widget_instance(patched)
        finally:
            cfg.user.setting[self._key_name] = original
        if widget is None:
            return
        self._prepare_widget(widget, patched)
        self._element_map = self._build_element_map(widget, patched)
        self._last_applied_values = (
            self._pending_values.copy() if self._pending_values else original.copy()
        )
        if forced_show and self._element_map:
            self._apply_show_hide(self._pending_values)
        self._inner_layout.insertWidget(0, widget)
        widget.show()
        self._active_widget = widget

    def _patch_config(self, original, pending):
        patched = copy.deepcopy(original)
        for key, value in pending.items():
            if key in patched:
                patched[key] = value
        return patched

    def _force_show_settings(self, config):
        """Force all show_* to True, return dict of originally-False ones"""
        forced = {}
        modified = config.copy()
        for key in config:
            if key.startswith("show_"):
                col_key = f"column_index_{key[5:]}"
                if col_key in config and not config[key]:
                    forced[key] = False
                    modified[key] = True
        return forced, modified

    def _build_element_map(self, widget, config):
        """Map show_* keys to (widget, column_index) for fast show/hide"""
        layout = widget.layout()
        if not isinstance(layout, QGridLayout):
            return {}
        is_vertical = config.get("layout", 0) == 0
        pos_to_widget = {}
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                row, col, _, _ = layout.getItemPosition(i)
                pos_to_widget[(row, col)] = item.widget()
        element_map = {}
        for key in config:
            if not key.startswith("show_"):
                continue
            col_key = f"column_index_{key[5:]}"
            if col_key not in config:
                continue
            col_idx = config[col_key]
            pos = (col_idx, 0) if is_vertical else (0, col_idx)
            w = pos_to_widget.get(pos)
            if w:
                element_map[key] = (w, col_idx)
        return element_map

    def _apply_show_hide(self, values):
        """Update element visibility without full rebuild"""
        if not self._element_map or not self._active_widget:
            return
        layout = self._active_widget.layout()
        if not isinstance(layout, QGridLayout):
            return
        is_vertical = self._active_widget.wcfg.get("layout", 0) == 0
        for _, (widget, _) in self._element_map.items():
            layout.removeWidget(widget)
        visible = []
        hidden = []
        for show_key, (widget, col_idx) in self._element_map.items():
            if values.get(show_key, True):
                visible.append((col_idx, widget))
            else:
                hidden.append((col_idx, widget))
        visible.sort(key=lambda x: x[0])
        hidden.sort(key=lambda x: x[0])
        idx = 0
        for _, widget in visible:
            widget.setVisible(True)
            if is_vertical:
                layout.addWidget(widget, idx, 0)
            else:
                layout.addWidget(widget, 0, idx)
            idx += 1
        for _, widget in hidden:
            widget.setVisible(False)
            if is_vertical:
                layout.addWidget(widget, idx, 0)
            else:
                layout.addWidget(widget, 0, idx)
            idx += 1


class _ConfigGrouper:
    """Group keys into sections based on show_* prefixes and word similarity"""

    MAX_TABLE_ROWS = 12
    MIN_REMAINING_ROWS = 4

    def __init__(self, min_match=2):
        self.min_match = min_match

    def _are_topics_similar(self, topic_a, topic_b):
        if topic_a in topic_b or topic_b in topic_a:
            return True
        words_a = set(topic_a.split("_"))
        words_b = set(topic_b.split("_"))
        return len(words_a & words_b) >= self.min_match

    def group_keys(self, keys):
        """Group keys into (title, key_list) sections"""
        fixed_groups = {}
        for key in keys:
            if key.startswith("column_index_"):
                fixed_groups.setdefault("Column Index", []).append(key)
        fixed_set = {k for group in fixed_groups.values() for k in group}
        remaining = [k for k in keys if k not in fixed_set]
        sections = []
        current_title = None
        current_keys = []
        last_show_topic = None
        for key in remaining:
            if key.startswith("show_"):
                topic = key[5:]
                if current_title is None:
                    current_title = topic
                    current_keys = [key]
                    last_show_topic = topic
                elif self._are_topics_similar(last_show_topic, topic):
                    current_keys.append(key)
                    last_show_topic = topic
                else:
                    sections.append((current_title, current_keys))
                    current_title = topic
                    current_keys = [key]
                    last_show_topic = topic
            else:
                if current_title is not None:
                    current_keys.append(key)
        if current_keys:
            sections.append((current_title, current_keys))
        assigned = set()
        for _, key_list in sections:
            assigned.update(key_list)
        unassigned = [k for k in remaining if k not in assigned]
        if unassigned:
            sections = [("", unassigned)] + sections
        for title, fkeys in fixed_groups.items():
            sections.append((title, fkeys))
        return sections

    def pack_sections(self, sections_data, max_rows=None, min_remaining=None):
        """Pack sections into batches that fit in tables"""
        if max_rows is None:
            max_rows = self.MAX_TABLE_ROWS
        if min_remaining is None:
            min_remaining = self.MIN_REMAINING_ROWS
        batches = []
        current_batch = []
        current_rows = 0
        for title, sec_keys in sections_data:
            section_size = len(sec_keys) + 1
            remaining = max_rows - current_rows
            if current_batch and (
                remaining < min_remaining
                or current_rows + section_size > max_rows
            ):
                batches.append(current_batch)
                current_batch = []
                current_rows = 0
            current_batch.append((title, sec_keys))
            current_rows += section_size
        if current_batch:
            batches.append(current_batch)
        return batches

    def _get_min_column_index(self, widget, current_values):
        keys = widget.property("section_keys") or []
        min_idx = 999999
        for key in keys:
            if key.startswith("column_index_"):
                val = current_values.get(key, 999999)
                if isinstance(val, (int, float)):
                    min_idx = min(min_idx, val)
        return min_idx

    def sort_widgets_by_column_index(self, widgets, current_values):
        """Sort a list of widgets in-place by their minimum column index"""
        widgets.sort(key=lambda w: self._get_min_column_index(w, current_values))


# ---- Private helper functions ----------------------------------------------

def _get_font_list():
    if os.getenv("PYSIDE_OVERRIDE") == "6":
        return QFontDatabase.families()
    return QFontDatabase().families()


def _add_context_menu(parent):
    parent.setContextMenuPolicy(Qt.CustomContextMenu)
    parent.customContextMenuRequested.connect(
        lambda pos, p=parent: _context_menu_reset(pos, p)
    )


def _context_menu_reset(position, parent):
    menu = QMenu()
    reset_action = menu.addAction("Reset to Default")
    action = menu.exec_(parent.mapToGlobal(position))
    if action == reset_action:
        parent.reset_to_default()


def _create_checkbox(parent, key, current_val, default_val, update_cb, choices):
    editor = QCheckBox(parent)
    editor.setChecked(bool(current_val))
    editor.stateChanged.connect(lambda state: update_cb(key, bool(state)))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setChecked(editor.defaults)
    _add_context_menu(editor)
    return editor


def _create_color_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = DoubleClickEdit(parent, mode="color", init=current_val)
    editor.setValidator(QVAL_COLOR)
    editor.textChanged.connect(editor.preview_color)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


def _create_path_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = DoubleClickEdit(parent, mode="path", init=current_val)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


def _create_image_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = DoubleClickEdit(parent, mode="image", init=current_val)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


def _create_font_combo(parent, key, current_val, default_val, update_cb, choices):
    editor = QComboBox(parent)
    editor.addItems(_get_font_list())
    editor.setCurrentText(str(current_val))
    editor.currentTextChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setCurrentText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


def _create_heatmap_combo(parent, key, current_val, default_val, update_cb, choices):
    editor = QComboBox(parent)
    if choices:
        editor.addItems(choices)
    editor.setCurrentText(str(current_val))
    editor.currentTextChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setCurrentText(str(editor.defaults))
    _add_context_menu(editor)
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
    editor.reset_to_default = lambda: editor.setCurrentText(str(editor.defaults))
    _add_context_menu(editor)
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
    editor.reset_to_default = lambda: editor.setCurrentText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


def _create_string_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = QLineEdit(parent)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


def _create_integer_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = QLineEdit(parent)
    editor.setValidator(QVAL_INTEGER)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


def _create_float_editor(parent, key, current_val, default_val, update_cb, choices):
    editor = QLineEdit(parent)
    editor.setValidator(QVAL_FLOAT)
    editor.setText(str(current_val))
    editor.textChanged.connect(partial(update_cb, key))
    editor.defaults = default_val
    editor.reset_to_default = lambda: editor.setText(str(editor.defaults))
    _add_context_menu(editor)
    return editor


_EDITOR_DISPATCH = [
    (rxp.CFG_BOOL, _create_checkbox),
    (rxp.CFG_COLOR, _create_color_editor),
    (rxp.CFG_USER_PATH, _create_path_editor),
    (rxp.CFG_USER_IMAGE, _create_image_editor),
    (rxp.CFG_FONT_NAME, _create_font_combo),
    (rxp.CFG_HEATMAP, _create_heatmap_combo),
]
for _ref in rxp.CHOICE_UNITS:
    _EDITOR_DISPATCH.append((_ref, _create_units_combo))
for _ref in rxp.CHOICE_COMMON:
    _EDITOR_DISPATCH.append((_ref, _create_common_combo))
_EDITOR_DISPATCH.extend([
    (rxp.CFG_CLOCK_FORMAT, _create_string_editor),
    (rxp.CFG_STRING, _create_string_editor),
    (rxp.CFG_INTEGER, _create_integer_editor),
])


def _create_editor(parent, key, current_val, default_val, update_cb, *, choices=None):
    """Create appropriate editor widget based on key pattern"""
    for pattern, factory in _EDITOR_DISPATCH:
        if re.search(pattern, key):
            return factory(parent, key, current_val, default_val, update_cb, choices)
    return _create_float_editor(parent, key, current_val, default_val, update_cb, choices)


def _validate_and_save(keys, current_values, target, editors, cfg_type, reload_func, error_callback):
    """Validate all values and save to config"""
    error_found = False

    for key in keys:
        value = current_values[key]

        if re.search(rxp.CFG_BOOL, key):
            target[key] = value
        elif re.search(rxp.CFG_COLOR, key):
            if is_hex_color(value):
                target[key] = value
            else:
                error_callback("color", key)
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
                error_callback("path", key)
                error_found = True
        elif re.search(rxp.CFG_USER_IMAGE, key):
            target[key] = value
        elif (re.search(rxp.CFG_FONT_NAME, key) or
              re.search(rxp.CFG_HEATMAP, key) or
              any(re.search(ref, key) for ref in rxp.CHOICE_UNITS) or
              any(re.search(ref, key) for ref in rxp.CHOICE_COMMON)):
            target[key] = value
        elif re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
            if re.search(rxp.CFG_CLOCK_FORMAT, key) and not is_clock_format(value):
                error_callback("clock format", key)
                error_found = True
            else:
                target[key] = value
        elif re.search(rxp.CFG_INTEGER, key):
            str_val = str(value)
            if is_string_number(str_val):
                target[key] = int(str_val)
            else:
                error_callback("number", key)
                error_found = True
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

    for key in keys:
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


# ---- Layout builder --------------------------------------------------------

class _LayoutBuilder:
    """Builds a vertical stack of rows"""

    def __init__(self, spacing=2, column_spacing=None, margins=(0, 0, 0, 0)):
        self._rows = []
        self._named_rows = {}
        self._spacing = spacing
        self._column_spacing = column_spacing if column_spacing is not None else spacing
        self._margins = margins

    def add(self, widget, *, name=None, stretch=0, scrollable=False):
        """Add a single widget as a row"""
        self._rows.append((widget, stretch, scrollable))
        if name:
            self._named_rows[name] = widget
        return self

    def addHorizontal(self, widgets, *, stretches=None,
                      name=None, stretch=0, scrollable=False):
        """Pack widgets side by side"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._column_spacing)
        if stretches is None:
            stretches = [1] * len(widgets)
        for w, s in zip(widgets, stretches):
            layout.addWidget(w, s)
        self._rows.append((container, stretch, scrollable))
        if name:
            self._named_rows[name] = container
        return self

    def addColumns(self, widgets, *, max_columns=5, compact_threshold=5,
                   name=None, stretch=1, scrollable=True):
        """Add a dynamic column grid row"""
        if len(widgets) <= compact_threshold:
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(self._column_spacing)
            for w in widgets:
                layout.addWidget(w)
            layout.addStretch(1)
            row = container
        else:
            row = _ColumnsRow(widgets, max_columns=max_columns, spacing=self._column_spacing)
        self._rows.append((row, stretch, scrollable))
        if name:
            self._named_rows[name] = row
        return self

    def row(self, name):
        """Retrieve a named row widget"""
        return self._named_rows.get(name)

    def build(self):
        """Create and return top-level container"""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(*self._margins)
        main_layout.setSpacing(self._spacing)
        for widget, stretch, scrollable in self._rows:
            if scrollable:
                scroll = QScrollArea()
                scroll.setWidget(widget)
                scroll.setWidgetResizable(True)
                scroll.setFrameShape(QScrollArea.NoFrame)
                main_layout.addWidget(scroll, stretch)
            else:
                main_layout.addWidget(widget, stretch)
        return container


# ---- Filter & highlight effects --------------------------------------------

class _FilterEffect:
    """Dims non-matching rows across tables and order lists"""

    def __init__(self):
        self._tables = []
        self._order_lists = []

    def add_table(self, table):
        self._tables.append(table)

    def add_order_list(self, order_list):
        self._order_lists.append(order_list)

    def apply(self, text):
        text = text.strip().lower()
        for table in self._tables:
            self._filter_table(table, text)
        for order_list in self._order_lists:
            order_list.apply_filter(text)

    def _filter_table(self, table, text):
        title_dimmed = (
            "background-color: palette(mid);"
            "color: palette(window);"
            "border-bottom: 2px solid palette(mid);"
            "padding: 4px;"
        )
        if not text:
            for key in table.keys():
                self._undim_row(table, key)
            if table.title_label is not None:
                table.title_label.setStyleSheet("")
            return
        all_dimmed = True
        for key in table.keys():
            if text in key.lower():
                self._undim_row(table, key)
                all_dimmed = False
            else:
                self._dim_row(table, key)
        if table.title_label is not None:
            table.title_label.setStyleSheet(
                title_dimmed if all_dimmed else "")

    @staticmethod
    def _dim_row(table, key):
        row = table.row_widget(key)
        if row is None:
            return
        row.setStyleSheet("background-color: palette(window);")
        label = table.row_label(key)
        if label is not None:
            label.setStyleSheet("color: palette(mid);")

    @staticmethod
    def _undim_row(table, key):
        row = table.row_widget(key)
        if row is None:
            return
        bg = row.property("_base_bg") or "palette(base)"
        row.setStyleSheet(f"background-color: {bg};")
        label = table.row_label(key)
        if label is not None:
            label.setStyleSheet("")


class _HighlightEffect:
    """Highlights rows by key across tables"""

    def __init__(self):
        self._tables = []
        self._active_keys = set()

    def add_table(self, table):
        self._tables.append(table)

    def apply(self, keys):
        self.clear()
        self._active_keys = set(keys)
        for table in self._tables:
            for key in self._active_keys:
                row = table.row_widget(key)
                if row:
                    row.setStyleSheet("background-color: lightblue;")

    def clear(self):
        if not self._active_keys:
            return
        for table in self._tables:
            for key in self._active_keys:
                row = table.row_widget(key)
                if row:
                    bg = row.property("_base_bg") or "palette(base)"
                    row.setStyleSheet(f"background-color: {bg};")
        self._active_keys.clear()


# ---- Public dialog class ---------------------------------------------------

@singleton_dialog(ConfigType.CONFIG)
class WidgetConfig(BaseDialog):
    """User config dialog"""

    def __init__(
        self,
        parent,
        key_name,
        cfg_type,
        user_setting,
        default_setting,
        reload_func,
        option_width=9,
        config_grouper=None,
    ):
        super().__init__(parent)
        try:
            self._init_attributes(key_name, cfg_type, user_setting, default_setting,
                                  reload_func, option_width, config_grouper)
            self._build_ui()
            self.adjust_to_screen()
        except Exception:
            import traceback
            traceback.print_exc()
            raise

    def _init_attributes(self, key_name, cfg_type, user_setting, default_setting,
                         reload_func, option_width, config_grouper):
        self.key_name = key_name
        self.cfg_type = cfg_type
        self.user_setting = user_setting
        self.default_setting = default_setting
        self.reloading = reload_func
        self.original_keys = list(self.user_setting[self.key_name])
        self._current_values = {
            key: self.user_setting[self.key_name][key] for key in self.original_keys
        }
        self._option_width = UIScaler.size(option_width)
        self._components = []
        self._editors = {}
        self._column_order_widgets = {}
        self._filter_effect = _FilterEffect()
        self._highlight_effect = _HighlightEffect()
        self._preview = (_WidgetPreview(self.key_name, parent=self)
                         if cfg_type == ConfigType.WIDGET else None)
        self._columns_zone = None
        self.grouper = config_grouper or _ConfigGrouper()
        # Window setup
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        preset = (f"{cfg.filename.config} (global)" if cfg_type == ConfigType.CONFIG
                  else cfg.filename.setting)
        self.set_config_title(format_option_name(key_name), preset)

    def _build_ui(self):
        """Build the complete UI"""
        general_table, column_widgets, self._section_widgets = self._build_grouped_content()
        # Search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type to filter options (Ctrl+F)")
        self._search.setClearButtonEnabled(True)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(
            lambda: self._filter_effect.apply(self._search.text().strip().lower())
        )
        self._search.textChanged.connect(lambda: self._search_timer.start(200))
        shortcut = QShortcut(QKeySequence.Find, self)
        shortcut.activated.connect(lambda: (self._search.setFocus(), self._search.selectAll()))
        # Assemble layout
        gap = UIScaler.pixel(10)
        builder = _LayoutBuilder(
            spacing=gap,
            column_spacing=UIScaler.pixel(5),
            margins=(gap, gap, gap, gap),
        )
        if self._preview is not None and self._preview.available:
            builder.add(self._preview, name='preview')
        builder.add(self._search, name='search')
        info_widgets = []
        if general_table is not None:
            info_widgets.append(general_table)
        info_widgets.extend(column_widgets)
        if info_widgets:
            builder.addHorizontal(info_widgets, name='info')
        builder.addColumns(
            self._section_widgets,
            max_columns=5,
            compact_threshold=1,
            name='content',
        )
        # Button bar (QDialogButtonBox)
        button_box = QDialogButtonBox()
        btn_reset = button_box.addButton("Reset widget", QDialogButtonBox.ResetRole)
        btn_reset.clicked.connect(self.factory_reset_widget)
        btn_save = button_box.addButton("Save", QDialogButtonBox.ApplyRole)
        btn_save.clicked.connect(self._save)
        btn_save_close = button_box.addButton("Save and Close", QDialogButtonBox.AcceptRole)
        btn_save_close.clicked.connect(self.safe_and_close)
        btn_cancel = button_box.addButton(QDialogButtonBox.Cancel)
        btn_cancel.clicked.connect(self.reject)
        builder.add(button_box)

        self._columns_zone = builder.row('content')
        main_widget = builder.build()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)

    def _build_grouped_content(self):
        """Build general table, drag and drop and rest of the option tables"""
        sections = self.grouper.group_keys(self.original_keys)
        general_table = None
        column_widgets = []
        sections_to_merge = []
        for title, sec_keys in sections:
            if all(k.startswith("column_index_") for k in sec_keys):
                sorted_keys = sorted(sec_keys, key=lambda k: self._current_values.get(k, 999))
                items = [(key, format_option_name(key[len("column_index_"):])) for key in sorted_keys]
                list_widget = _DragDropOrderList(items=items, row_height=ROW_HEIGHT, parent=self)
                if title is not None:
                    list_widget.set_title(
                        format_option_name(self.key_name) if title == "" else "Sections")
                list_widget.itemClicked.connect(self.highlight_section)
                list_widget.orderChanged.connect(self._handle_column_reorder)
                for key in sec_keys:
                    self._column_order_widgets[key] = list_widget
                self._filter_effect.add_order_list(list_widget)
                column_widgets.append(list_widget)
            elif title == "" and general_table is None:
                general_table = self._build_option_table([(title, sec_keys)], columns=2)
            else:
                sections_to_merge.append((title, sec_keys))
        batches = self.grouper.pack_sections(sections_to_merge)
        merged_widgets = [self._build_option_table(batch) for batch in batches]
        self.grouper.sort_widgets_by_column_index(merged_widgets, self._current_values)
        return general_table, column_widgets, merged_widgets

    def _build_option_table(self, sections, columns=1):
        """Build an _OptionTable for one or more sections"""
        table = _OptionTable(
            parent=self, columns=columns,
            row_height=ROW_HEIGHT, editor_width=self._option_width,
        )
        if len(sections) == 1:
            title, keys = sections[0]
            if title is not None:
                display = (format_option_name(self.key_name) if title == ""
                           else format_option_name(title))
                table.set_title(display)
            for key in keys:
                editor = self._make_editor(key)
                table.add_row(key, format_option_name(key), editor)
                self._editors[key] = editor
        else:
            for title, sec_keys in sections:
                table.add_section_header(format_option_name(title))
                for key in sec_keys:
                    editor = self._make_editor(key)
                    table.add_row(key, format_option_name(key), editor)
                    self._editors[key] = editor
        table.setProperty("section_keys", table.keys())
        self._filter_effect.add_table(table)
        self._highlight_effect.add_table(table)
        return table

    def _handle_column_reorder(self, new_order):
        """Update column indexes and re-sort section widgets"""
        for index, key in enumerate(new_order, start=1):
            self._update_current_value(key, index)
        self.grouper.sort_widgets_by_column_index(self._section_widgets, self._current_values)
        if isinstance(self._columns_zone, _ColumnsRow):
            self._columns_zone.setWidgets(self._section_widgets[:])

    def _make_editor(self, key):
        return _create_editor(
            self, key,
            self._current_values[key],
            self.default_setting[self.key_name][key],
            self._update_current_value,
        )

    def _update_current_value(self, key, value):
        self._current_values[key] = value
        if self._preview is not None:
            self._preview.schedule_refresh(self._current_values)

    def highlight_section(self, column_key):
        """Highlight all options belonging to same section"""
        for title, keys in self.grouper.group_keys(self.original_keys):
            if column_key in keys:
                self._highlight_effect.apply(keys)
                break

    def safe_and_close(self):
        """Save & close"""
        if self._save():
            self.accept()

    def _save(self):
        """Validate and save all values"""
        target = self.user_setting[self.key_name]
        return _validate_and_save(
            self.original_keys,
            self._current_values,
            target,
            self._editors,
            self.cfg_type,
            self.reloading,
            self._show_validation_error,
        )

    def factory_reset_widget(self):
        """Reset all options to defaults"""
        msg = (
            f"Reset all <b>{format_option_name(self.key_name)}</b> options to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if not self.confirm_operation(title="Reset Options", message=msg):
            return
        for key, editor in self._editors.items():
            editor.reset_to_default()
            self._current_values[key] = editor.defaults
        seen = set()
        for key, list_widget in self._column_order_widgets.items():
            if id(list_widget) not in seen:
                seen.add(id(list_widget))
                all_keys = [k for k, w in self._column_order_widgets.items() if w is list_widget]
                default_vals = {
                    k: self.default_setting[self.key_name][k] for k in all_keys
                }
                list_widget.reset_to_defaults(default_vals)

    def _show_validation_error(self, value_type, option_name):
        msg = (
            f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg)

    def _cleanup(self):
        self._search_timer.stop()
        if self._preview is not None:
            self._preview.cleanup()

    def reject(self):
        self._cleanup()
        super().reject()

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)
