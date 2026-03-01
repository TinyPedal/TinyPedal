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
from .effects import FilterEffect, HighlightEffect
from .helpers.config_grouper import ConfigGrouper
from .helpers.config_saver import validate_and_save
from .helpers.layout_builder import LayoutBuilder, ColumnsRow


ROW_HEIGHT = UIScaler.size(3)


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
        self._filter_effect = FilterEffect()
        self._highlight_effect = HighlightEffect()
        self._preview = (WidgetPreview(self.key_name, parent=self)
                         if cfg_type == ConfigType.WIDGET else None)
        self._columns_zone = None
        self.grouper = config_grouper or ConfigGrouper()
        # Window setup
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        preset = (f"{cfg.filename.config} (global)" if cfg_type == ConfigType.CONFIG
                  else cfg.filename.setting)
        self.set_config_title(format_option_name(key_name), preset)

    def _build_ui(self):
        """Build the complete UI"""
        general_table, column_widgets, self._section_widgets = self._build_grouped_content()
        # Search bar
        self._search = SearchBar(parent=self)
        self._search.filterRequested.connect(self._filter_effect.apply)
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
        # Button bar
        bar = ButtonBar()
        bar.add_left("Reset widget", self.factory_reset_widget)
        bar.add_right("Safe", self._save)
        bar.add_right("Safe and Close", self.safe_and_close)
        bar.add_right("Cancel", self.reject)
        builder.add(bar)
        self._columns_zone = builder.row('content')
        main_widget = builder.build()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)

    def _build_grouped_content(self):
        """Build general table, drag and drop and rest op the option tables"""
        sections = self.grouper.group_keys(self.original_keys)
        general_table = None
        column_widgets = []
        sections_to_merge = []
        for title, sec_keys in sections:
            if all(k.startswith("column_index_") for k in sec_keys):
                # Column order drag-drop list
                sorted_keys = sorted(sec_keys, key=lambda k: self._current_values.get(k, 999))
                items = [(key, format_option_name(key[len("column_index_"):])) for key in sorted_keys]
                list_widget = DragDropOrderList(items=items, row_height=ROW_HEIGHT, parent=self)
                if title is not None:
                    list_widget.set_title(
                        format_option_name(self.key_name) if title == "" else "Sections")
                list_widget.itemClicked.connect(self.highlight_section)
                list_widget.orderChanged.connect(self._handle_column_reorder)
                for key in sec_keys:
                    self._column_order_widgets[key] = list_widget
                self._components.append(list_widget)
                self._filter_effect.add_order_list(list_widget)
                column_widgets.append(list_widget)
            elif title == "" and general_table is None:
                general_table = self._build_option_table([(title, sec_keys)], columns=2)
            else:
                sections_to_merge.append((title, sec_keys))
        # Pack sections into batches
        batches = self.grouper.pack_sections(sections_to_merge)
        merged_widgets = [self._build_option_table(batch) for batch in batches]
        self.grouper.sort_widgets_by_column_index(merged_widgets, self._current_values)
        return general_table, column_widgets, merged_widgets

    def _build_option_table(self, sections, columns=1):
        """Build an OptionTable for one or more sections"""
        table = OptionTable(
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
                editor = self._create_editor(key)
                table.add_row(key, format_option_name(key), editor)
                self._editors[key] = editor
        else:
            for title, sec_keys in sections:
                table.add_section_header(format_option_name(title))
                for key in sec_keys:
                    editor = self._create_editor(key)
                    table.add_row(key, format_option_name(key), editor)
                    self._editors[key] = editor
        table.setProperty("section_keys", table.keys())
        self._components.append(table)
        self._filter_effect.add_table(table)
        self._highlight_effect.add_table(table)
        return table

    def _handle_column_reorder(self, new_order):
        """Update column indexes and re-sort section widgets"""
        for index, key in enumerate(new_order, start=1):
            self._update_current_value(key, index)
        self.grouper.sort_widgets_by_column_index(self._section_widgets, self._current_values)
        if isinstance(self._columns_zone, ColumnsRow):
            self._columns_zone.setWidgets(self._section_widgets[:])

    def _create_editor(self, key):
        return create_editor(
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
        return validate_and_save(
            self.original_keys,
            self._current_values,
            target,
            self._editors,
            self.cfg_type,
            self.reloading,
            self._show_validation_error,  # pass error callback
        )

    def factory_reset_widget(self):
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

    def _show_validation_error(self, value_type, option_name):
        msg = (
            f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg)

    def _cleanup(self):
        for comp in self._components:
            comp.cleanup()

    def reject(self):
        self._cleanup()
        super().reject()

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)
