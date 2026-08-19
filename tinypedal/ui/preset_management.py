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
Preset management
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from types import MappingProxyType

from PySide2.QtGui import QColor
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)

from .. import app_signal
from .. import regex_pattern as rxp
from ..const_file import ConfigType, FileExt
from ..formatter import format_option_name, strip_filename_extension
from ..setting import cfg, load_setting_json_file, save_and_verify_json_file
from ..template.setting_shortcuts import SHORTCUTS_PRESET
from ..userfile.json_setting import verify_json_file
from ..validator import is_allowed_filename
from ._common import QVAL_FILENAME, BaseDialog, BaseEditor, CompactButton, UIScaler

logger = logging.getLogger(__name__)


class CreatePreset(BaseDialog):
    """Create preset"""

    def __init__(self, parent, title: str = "", mode: str = "", source_filename: str = ""):
        """Initialize create preset dialog setting

        Args:
            title: Dialog title string.
            mode: Edit mode, either "duplicate", "restore", "rename", or "" for new preset.
            source_filename: Source setting filename.
        """
        super().__init__(parent)
        self.edit_mode = mode
        self.source_filename = source_filename

        self.setWindowTitle(title)

        # Entry box
        self.preset_entry = QLineEdit()
        self.preset_entry.setMaxLength(40)
        self.preset_entry.setPlaceholderText("Enter a new preset name")
        self.preset_entry.setValidator(QVAL_FILENAME)

        # Button
        button_create = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_create.accepted.connect(self.create)
        button_create.rejected.connect(self.reject)

        # Layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.preset_entry)
        layout_main.addWidget(button_create)
        self.setLayout(layout_main)
        self.setMinimumWidth(UIScaler.size(21))
        self.setFixedHeight(self.sizeHint().height())

    def create(self):
        """Create & save new preset"""
        entered_filename = strip_filename_extension(self.preset_entry.text(), FileExt.JSON)
        source_filename = self.source_filename
        filepath = cfg.path.settings
        # Check invalid file name
        if not is_allowed_filename(entered_filename):
            QMessageBox.warning(self, "Error", "Invalid preset name.")
            return
        # Check existing preset
        temp_list = cfg.preset_files()
        for preset in temp_list:
            if entered_filename.lower() == preset.lower():
                QMessageBox.warning(self, "Error", "Preset already exists.")
                return
        # Duplicate preset
        if self.edit_mode == "duplicate":
            shutil.copy(
                f"{filepath}{source_filename}",
                f"{filepath}{entered_filename}{FileExt.JSON}"
            )
        # Restore preset
        elif self.edit_mode == "restore":
            os.rename(
                f"{filepath}{source_filename}",
                f"{filepath}{entered_filename}{FileExt.JSON}"
            )
        # Rename preset
        elif self.edit_mode == "rename":
            os.rename(
                f"{filepath}{source_filename}",
                f"{filepath}{entered_filename}{FileExt.JSON}"
            )
            # Rename matching preset shortcut
            source_name = source_filename[:-5]
            for option_name in SHORTCUTS_PRESET:
                preset_name = cfg.user.shortcuts[option_name]["preset"]
                if source_name == preset_name:
                    cfg.user.shortcuts[option_name]["preset"] = entered_filename
                    cfg.save(config_type=ConfigType.SHORTCUTS)
            # Reload if renamed file was loaded
            if cfg.is_loaded(source_filename):
                cfg.set_next_to_load(f"{entered_filename}{FileExt.JSON}")
                app_signal.reload.emit(True)
                self.accept()
                return
        # Create new preset
        else:
            cfg.create(f"{entered_filename}{FileExt.JSON}")
        # Close window
        app_signal.refresh.emit(True)
        self.accept()


class RestoreBackup(BaseEditor):
    """Restore backup"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Restore Backup")
        self.setMinimumSize(UIScaler.size(40), UIScaler.size(20))

        # Backup list
        self.listbox_backup = QListWidget(self)
        self.listbox_backup.setAlternatingRowColors(True)

        # Button
        button_restore = CompactButton("Restore")
        button_restore.clicked.connect(self.restore)

        button_refresh = CompactButton("Refresh")
        button_refresh.clicked.connect(self.refresh)

        button_delete = CompactButton("Delete")
        button_delete.clicked.connect(self.delete)

        button_close = CompactButton("Close")
        button_close.clicked.connect(self.close)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_restore)
        layout_button.addWidget(button_refresh)
        layout_button.addWidget(button_delete)
        layout_button.addStretch(1)
        layout_button.addWidget(button_close)

        # Set layout
        layout_main = QGridLayout()
        layout_main.addWidget(self.listbox_backup, 2, 1)
        layout_main.addLayout(layout_button, 3, 1)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)
        self.refresh()

    def refresh(self):
        """Load backup file list"""
        self.listbox_backup.clear()
        backup_list = cfg.backup_files(cfg.path.settings)
        invalid_color = QColor("#F40")
        style_color = QColor("#08F")

        for backup_name in backup_list:
            basename = backup_name[:backup_name.find(FileExt.JSON)]
            if not basename:  # ignore empty file
                continue
            item = QListWidgetItem()
            item.setText(backup_name)
            item.is_valid = verify_json_file(None, backup_name, cfg.path.settings)
            item.is_style = not is_allowed_filename(basename)
            if not item.is_valid:
                item.setForeground(invalid_color)
            elif item.is_style:
                item.setForeground(style_color)
            self.listbox_backup.addItem(item)

    def is_selected(self) -> bool:
        """Is file selected"""
        if not self.listbox_backup.selectedIndexes():
            msg_text = "No backup file selected."
            QMessageBox.warning(self, "Error", msg_text)
            return False
        return True

    def delete(self):
        """Delete backup file"""
        if not self.is_selected():
            return

        selected_item = self.listbox_backup.currentItem()
        selected_filename = selected_item.text()
        msg_text = (
            f"Delete <b>{selected_filename}</b> preset permanently?<br><br>"
            "This cannot be undone!"
        )
        if self.confirm_operation(title="Delete Preset", message=msg_text):
            full_path = f"{cfg.path.settings}{selected_filename}"
            if os.path.exists(full_path):
                os.remove(full_path)
                self.refresh()

    def restore(self):
        """Restore backup file"""
        if not self.is_selected():
            return

        selected_item = self.listbox_backup.currentItem()
        if not selected_item.is_valid:
            msg_text = "Selected backup file is invalid and cannot be restored."
            QMessageBox.warning(self, "Error", msg_text)
            return

        selected_filename = selected_item.text()

        # Style preset
        if selected_item.is_style:
            msg_text = (
                f"<b>{selected_filename}</b> is a style preset.<br>"
                "Restoring this backup file will overwrite existing style preset.<br><br>"
                "Are you sure you want to restore and overwrite existing style preset?<br><br>"
                "This cannot be undone!"
            )
            if self.confirm_operation(title="Restore Style Preset", message=msg_text):
                basename = selected_filename[:selected_filename.find(FileExt.JSON)]
                filepath = cfg.path.settings
                shutil.move(
                    f"{filepath}{selected_filename}",
                    f"{filepath}{basename}{FileExt.JSON}"
                )
                app_signal.reload.emit(True)
                self.refresh()
            return

        # User preset
        _dialog = CreatePreset(
            self,
            title="Restore Backup",
            mode="restore",
            source_filename=selected_filename
        )
        _dialog.accepted.connect(self.refresh)
        _dialog.open()


class PresetTransfer(BaseEditor):
    """Preset Transfer"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Preset Transfer")
        self.setMinimumSize(UIScaler.size(40), UIScaler.size(38))

        # Label
        self.loaded_preset = cfg.filename.setting[:-5]
        label_loaded = QLabel(f"From: <b>{self.loaded_preset}</b>")

        # Setting list
        self.listbox_setting = QListWidget(self)
        self.set_setting_list(self.listbox_setting, cfg.user.setting)

        # Preset selector
        self.dest_selector = QComboBox()
        self.dest_selector.addItems(self.set_selector_list())

        # Option type list
        self.listbox_options = QListWidget(self)
        option_types = (
            "enable_state",
            "feature_toggle",
            "update_interval",
            "position",
            "opacity",
            "layout",
            "color",
            "font",
            "prefix_and_suffix",
            "caption_text",
            "decimal_places",
            "display_order",
            "other_options",
        )
        self.set_setting_list(self.listbox_options, option_types)
        layout_dest = QHBoxLayout()
        layout_dest.addWidget(QLabel("To:"))
        layout_dest.addWidget(self.dest_selector, stretch=1)

        # Button transfer
        button_apply = CompactButton("Transfer")
        button_apply.clicked.connect(self.transfer)

        button_close = CompactButton("Close")
        button_close.clicked.connect(self.close)

        layout_button = QHBoxLayout()
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_close)

        # List header
        header_setting = ListHeader(self, "Setting", self.listbox_setting)
        header_options = ListHeader(self, "Option Type", self.listbox_options)

        # Set layout
        layout_main = QGridLayout()
        layout_main.addWidget(label_loaded, 0, 0)
        layout_main.addWidget(header_setting, 1, 0)
        layout_main.addWidget(self.listbox_setting, 2, 0)
        layout_main.addLayout(layout_dest, 0, 1)
        layout_main.addWidget(header_options, 1, 1)
        layout_main.addWidget(self.listbox_options, 2, 1)
        layout_main.addLayout(layout_button, 3, 1)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)

    def set_selector_list(self) -> list:
        """Set preset selector list"""
        preset_list = cfg.preset_files()
        # Remove loaded preset
        if self.loaded_preset in preset_list:
            preset_list.remove(self.loaded_preset)
        # Remove locked preset
        for name in reversed(preset_list):
            full_name = f"{name}.json"
            if full_name in cfg.user.filelock:
                preset_list.remove(name)
        return preset_list

    def set_setting_list(self, listbox: QListWidget, settings: tuple | dict):
        """Set setting list"""
        for setting_name in settings:
            item = QListWidgetItem()
            listbox.addItem(item)
            checkbox_item = QCheckBox(self)
            checkbox_item.setText(format_option_name(setting_name))
            checkbox_item.key_name = setting_name
            listbox.setItemWidget(item, checkbox_item)

    def get_setting_selection(self, listbox: QListWidget):
        """Get setting selection"""
        for row_index in range(listbox.count()):
            item = listbox.item(row_index)
            checkbox = listbox.itemWidget(item)
            if checkbox.isChecked():
                yield checkbox.key_name

    def transfer(self):
        """Transfer setting"""
        if not self.dest_selector.currentText():
            msg_text = "No destination preset selected or found."
            QMessageBox.warning(self, "Error", msg_text)
            return
        loaded_preset_name = f"{self.loaded_preset}.json"
        dest_preset_name = f"{self.dest_selector.currentText()}.json"
        setting_selection = tuple(self.get_setting_selection(self.listbox_setting))
        if not setting_selection:
            msg_text = "No preset setting selected.<br><br>Select at least one setting and try again."
            QMessageBox.warning(self, "Error", msg_text)
            return
        options_selection = tuple(self.get_setting_selection(self.listbox_options))
        if not options_selection:
            msg_text = "No option type selected.<br><br>Select at least one option type and try again."
            QMessageBox.warning(self, "Error", msg_text)
            return
        msg_text = (
            f"Transfer selected settings from <b>{loaded_preset_name}</b>"
            f" to <b>{dest_preset_name}</b>?<br><br>"
            "This cannot be undone!"
        )
        if not self.confirm_operation(message=msg_text):
            return
        # Load preset dict
        dest_dict = load_setting_json_file(
            filename=dest_preset_name,
            filepath=cfg.path.settings,
            dict_def=cfg.default.setting,
        )
        # Copy setting
        self.copy_setting(dest_dict, setting_selection, options_selection)
        # Save setting
        save_and_verify_json_file(
            dict_user=dest_dict,
            filename=dest_preset_name,
            filepath=cfg.path.settings,
            max_attempts=cfg.max_saving_attempts,
        )
        msg_text = (
            f"Settings are transferred from <b>{loaded_preset_name}</b>"
            f" to <b>{dest_preset_name}</b>."
        )
        QMessageBox.information(self, "Transfer Completed", msg_text)

    def copy_setting(self, dest_dict: dict, setting_selection: tuple[str, ...], options_selection: tuple[str, ...]):
        """Copy setting"""
        source_dict = MappingProxyType(cfg.user.setting)
        for setting_name, source_setting_dict in source_dict.items():
            if setting_name not in setting_selection:
                continue
            dest_setting_dict = dest_dict[setting_name]
            for option_name, option_value in source_setting_dict.items():
                if "enable" == option_name:
                    if "enable_state" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search(rxp.CFG_BOOL, option_name):
                    if "feature_toggle" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search("update_interval", option_name):
                    if "update_interval" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search("^position_x$|^position_y$", option_name):
                    if "position" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if "opacity" == option_name:
                    if "opacity" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if "layout" == option_name:
                    if "layout" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search(rxp.CFG_COLOR, option_name):
                    if "color" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search("font_name|font_weight|font_size|font_offset", option_name):
                    if "font" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search("prefix|suffix", option_name):
                    if "prefix_and_suffix" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search("caption_text", option_name):
                    if "caption_text" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search("display_order", option_name):
                    if "display_order" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if re.search("decimal_places", option_name):
                    if "decimal_places" in options_selection:
                        dest_setting_dict[option_name] = option_value
                    continue
                if "other_options" in options_selection:
                    dest_setting_dict[option_name] = option_value
                    continue


class ListHeader(QFrame):
    """List header"""

    def __init__(self, parent, title: str, listbox: QListWidget):
        super().__init__(parent)
        self._parent = parent
        self._listbox = listbox
        self._title = title

        button_selectall = CompactButton(" All ")
        button_selectall.clicked.connect(self.button_select_all)

        button_deselectall = CompactButton("None")
        button_deselectall.clicked.connect(self.button_deselect_all)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(f"Select {title}"))
        layout.addWidget(button_selectall)
        layout.addWidget(button_deselectall)
        self.setLayout(layout)
        self.setFrameShape(QFrame.StyledPanel)

    def button_select_all(self):
        """Select all check box"""
        msg_text = f"Select all {self._title}s from list?"
        if self._parent.confirm_operation(message=msg_text):
            self.set_selection(self._listbox, True)

    def button_deselect_all(self):
        """Deselect all check box"""
        msg_text = f"Deselect all {self._title}s from list?"
        if self._parent.confirm_operation(message=msg_text):
            self.set_selection(self._listbox, False)

    def set_selection(self, listbox: QListWidget, checked: bool):
        """Set check box"""
        for row_index in range(listbox.count()):
            item = listbox.item(row_index)
            listbox.itemWidget(item).setChecked(checked)
