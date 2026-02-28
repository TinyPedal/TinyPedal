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

"""Config dialog"""

from __future__ import annotations

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMessageBox, QVBoxLayout

from ..const_file import ConfigType
from ..formatter import format_option_name
from ..setting import cfg
from ._common import BaseDialog, UIScaler, singleton_dialog
from .components.button_bar import ButtonBar
from .components.drag_drop_list import DragDropOrderList
from .components.option_editors import create_editor
from .components.preview import WidgetPreview
from .components.search_bar import SearchBar
from .components.table import OptionTable
from .helpers.config_grouper import ConfigGrouper
from .helpers.config_saver import validate_and_save
from .helpers.layout_builder import LayoutBuilder, ColumnsRow


ROW_HEIGHT = UIScaler.size(3)


def set_preset_name(cfg_type):
    """Set preset name"""
    if cfg_type == ConfigType.CONFIG:
        return f"{cfg.filename.config} (global)"
    return cfg.filename.setting


@singleton_dialog(ConfigType.CONFIG)
class UserConfig(BaseDialog):
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
            self._setup_window()
            self._create_preview_if_needed()
            self._build_ui()
            self._adjust_window_size()
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
        self._highlighted_keys = set()
        self._preview = None
        self._columns_zone = None
        self.grouper = config_grouper or ConfigGrouper()

    def _setup_window(self):
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.set_config_title(format_option_name(self.key_name),
                              set_preset_name(self.cfg_type))

    def _create_preview_if_needed(self):
        if self.cfg_type == ConfigType.WIDGET:
            self._preview = WidgetPreview(self.key_name, parent=self)

    def _build_ui(self):
        """Build the complete UI"""
        general_table, column_widgets, section_widgets = self._build_all_sections()
        self._section_widgets = section_widgets
        # Search bar
        self._search = SearchBar(parent=self)
        self._search.filterRequested.connect(self._on_filter)
        self._components.append(self._search)
        if self._preview is not None:
            self._components.append(self._preview)
        # Assemble layout
        gap = UIScaler.pixel(10)
        builder = LayoutBuilder(
            spacing=gap,
            column_spacing=UIScaler.pixel(5),
            margins=(gap, gap, gap, gap),
        )
        if self._preview is not None and self._preview.available:
            builder.add(self._preview, name='preview')
        info_widgets = []
        if general_table is not None:
            info_widgets.append(general_table)
        info_widgets.extend(column_widgets)
        if info_widgets:
            builder.addHorizontal(info_widgets, name='info')
        builder.add(self._search, name='search')
        builder.addColumns(
            self._section_widgets,
            max_columns=5,
            compact_threshold=1,
            name='content',
        )
        builder.add(self._build_button_bar())
        self._columns_zone = builder.row('content')
        main_widget = builder.build()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)

    def _build_button_bar(self):
        """Create button bar"""
        bar = ButtonBar()
        bar.add_left("Reset", self.reset_setting)
        bar.add_right("Apply", self.applying)
        bar.add_right("Save", self.saving)
        bar.add_right("Cancel", self.reject)
        return bar

    def _build_all_sections(self):
        """Build general table, column order widgets, and section tables"""
        sections = self.grouper.group_keys(self.original_keys)
        general_table = None
        column_widgets = []
        sections_to_merge = []
        for title, sec_keys in sections:
            if all(k.startswith("column_index_") for k in sec_keys):
                column_widgets.append(self._build_column_order_widget(title, sec_keys))
            elif title == "" and general_table is None:
                general_table = self._build_table(title, sec_keys, columns=2)
            else:
                sections_to_merge.append((title, sec_keys))
        # Pack sections into batches
        batches = self.grouper.pack_sections(sections_to_merge)
        merged_widgets = [self._build_merged_table(batch) for batch in batches]
        # Sort the widgets by column index
        self.grouper.sort_widgets_by_column_index(merged_widgets, self._current_values)
        return general_table, column_widgets, merged_widgets

    def _build_table(self, title, keys, columns=1):
        """Build an OptionTable for given keys"""
        table = OptionTable(
            parent=self, columns=columns,
            row_height=ROW_HEIGHT, editor_width=self._option_width,
        )
        if title is not None:
            display = (format_option_name(self.key_name) if title == ""
                       else format_option_name(title))
            table.set_title(display)
        for key in keys:
            editor = self._create_editor(key)
            table.add_row(key, format_option_name(key), editor)
            self._editors[key] = editor
        self._components.append(table)
        return table

    def _build_merged_table(self, sections_data):
        """Build a table containing multiple sections with headers"""
        table = OptionTable(
            parent=self, columns=1,
            row_height=ROW_HEIGHT, editor_width=self._option_width,
        )
        all_keys = []
        for title, sec_keys in sections_data:
            table.add_section_header(format_option_name(title))
            for key in sec_keys:
                editor = self._create_editor(key)
                table.add_row(key, format_option_name(key), editor)
                self._editors[key] = editor
            all_keys.extend(sec_keys)
        table.setProperty("section_keys", all_keys)
        self._components.append(table)
        return table

    def _build_column_order_widget(self, title, keys):
        """Build drag-and-drop column order list"""
        # Sort by current order
        sorted_keys = sorted(keys, key=lambda k: self._current_values.get(k, 999))
        items = [
            (key, format_option_name(key[len("column_index_"):]))
            for key in sorted_keys
        ]
        list_widget = DragDropOrderList(items=items, row_height=ROW_HEIGHT, parent=self)
        if title is not None:
            list_widget.set_title(format_option_name(self.key_name) if title == "" else "Sections")
        list_widget.itemClicked.connect(self.highlight_section)
        list_widget.orderChanged.connect(self._handle_column_reorder)
        for key in keys:
            self._column_order_widgets[key] = list_widget
        self._components.append(list_widget)
        return list_widget

    def _handle_column_reorder(self, new_order):
        """Update column indexes after reorder"""
        for index, key in enumerate(new_order, start=1):
            self._update_current_value(key, index)
        self._on_column_order_changed()

    def _create_editor(self, key):
        return create_editor(
            self, key,
            self._current_values[key],
            self.default_setting[self.key_name][key],
            self._update_current_value,
        )

    def _on_column_order_changed(self):
        self.grouper.sort_widgets_by_column_index(self._section_widgets, self._current_values)
        if isinstance(self._columns_zone, ColumnsRow):
            self._columns_zone.setWidgets(self._section_widgets[:])

    def _update_current_value(self, key, value):
        self._current_values[key] = value
        if self._preview is not None:
            self._preview.schedule_refresh(self._current_values)

    def _on_filter(self, text):
        """Apply filter to all components"""
        for comp in self._components:
            comp.apply_filter(text)

    def highlight_section(self, column_key):
        """Highlight all options belonging to same section"""
        for title, keys in self.grouper.group_keys(self.original_keys):
            if column_key in keys:
                self._clear_highlight()
                self._highlighted_keys = set(keys)
                for comp in self._components:
                    comp.highlight_keys(self._highlighted_keys)
                break

    def _clear_highlight(self):
        if self._highlighted_keys:
            for comp in self._components:
                comp.clear_highlight(self._highlighted_keys)
            self._highlighted_keys.clear()

    def applying(self):
        """Save & apply"""
        self._save_setting()

    def saving(self):
        """Save & close"""
        if self._save_setting():
            self.accept()

    def _save_setting(self):
        """Validate and save all values"""
        target = self.user_setting[self.key_name]
        return validate_and_save(
            self.original_keys,
            self._current_values,
            target,
            self._editors,
            self.cfg_type,
            self.reloading,
            self._value_error,  # pass error callback
        )

    def reset_setting(self):
        """Reset all options to defaults"""
        msg = (
            f"Reset all <b>{format_option_name(self.key_name)}</b> options to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if not self.confirm_operation(title="Reset Options", message=msg):
            return
        # Reset editors
        for key, editor in self._editors.items():
            editor.reset_to_default()
            self._current_values[key] = editor.defaults
        # Reset column order lists
        seen = set()
        for key, list_widget in self._column_order_widgets.items():
            if id(list_widget) not in seen:
                seen.add(id(list_widget))
                all_keys = [k for k, w in self._column_order_widgets.items() if w is list_widget]
                default_vals = {
                    k: self.default_setting[self.key_name][k] for k in all_keys
                }
                list_widget.reset_to_defaults(default_vals)

    def _value_error(self, value_type, option_name):
        msg = (
            f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg)

    def _adjust_window_size(self):
        """Size window to content, capped at 85% of screen"""
        self.adjustSize()
        try:
            avail = self.screen().availableGeometry()
            max_w = int(avail.width() * 0.85)
            max_h = int(avail.height() * 0.85)
        except AttributeError:
            max_w = 1400
            max_h = 800
        self.resize(min(self.width(), max_w), min(self.height(), max_h))

    def _cleanup(self):
        for comp in self._components:
            comp.cleanup()

    def reject(self):
        self._cleanup()
        super().reject()

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)
