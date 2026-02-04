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
Preset list view
"""

import os
import shutil

from PySide2.QtCore import QPoint, Qt, Slot
from PySide2.QtWidgets import (
    QCheckBox,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import app_signal
from ..const_app import VERSION
from ..const_file import ConfigType, FileExt
from ..formatter import strip_filename_extension
from ..setting import cfg
from ..validator import is_allowed_filename
from ._common import QVAL_FILENAME, BaseDialog, UIScaler
from .preset_transfer import PresetTransfer


class PresetList(QWidget):
    """Preset list view"""

    def __init__(self, parent):
        super().__init__(parent)
        # Label
        self.label_loaded = QLabel("")

        # Button
        button_refresh = QPushButton("Refresh")
        button_refresh.clicked.connect(self.refresh)

        button_transfer = QPushButton("Transfer")
        button_transfer.clicked.connect(self.open_preset_transfer)

        button_create = QPushButton("New Preset")
        button_create.clicked.connect(self.open_create_preset)

        # Check box
        self.checkbox_autoload = QCheckBox("Auto Load Primary Preset")
        self.checkbox_autoload.setChecked(cfg.application["enable_auto_load_preset"])
        self.checkbox_autoload.toggled.connect(self.toggle_autoload)

        # List box
        self.listbox_preset = QListWidget(self)
        self.listbox_preset.setAlternatingRowColors(True)
        self.listbox_preset.itemDoubleClicked.connect(self.load_preset)
        self.listbox_preset.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listbox_preset.customContextMenuRequested.connect(self.open_context_menu)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_refresh)
        layout_button.addWidget(button_transfer)
        layout_button.addStretch(1)
        layout_button.addWidget(button_create)

        # Layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.label_loaded)
        layout_main.addWidget(self.listbox_preset)
        layout_main.addWidget(self.checkbox_autoload)
        layout_main.addLayout(layout_button)
        margin = UIScaler.pixel(6)
        layout_main.setContentsMargins(margin, margin, margin, margin)
        self.setLayout(layout_main)

    @Slot(bool)  # type: ignore[operator]
    def refresh(self):
        """Refresh preset list"""
        preset_list = cfg.preset_files()
        self.listbox_preset.clear()

        for preset_name in preset_list:
            # Add preset name
            item = QListWidgetItem()
            item.setText(preset_name)
            self.listbox_preset.addItem(item)
            # Add primary preset tag
            label_item = PresetTagItem(None, preset_name)
            self.listbox_preset.setItemWidget(item, label_item)

        loaded_preset = cfg.filename.setting
        locked_tag = " (locked)" if loaded_preset in cfg.user.filelock else ""
        self.label_loaded.setText(f"Loaded: <b>{loaded_preset[:-5]}{locked_tag}</b>")
        self.checkbox_autoload.setChecked(cfg.application["enable_auto_load_preset"])

    def load_preset(self):
        """Load selected preset"""
        selected_index = self.listbox_preset.currentRow()
        if selected_index >= 0:
            selected_preset_name = self.listbox_preset.item(selected_index).text()
            cfg.set_next_to_load(f"{selected_preset_name}{FileExt.JSON}")
            app_signal.reload.emit(True)
        else:
            QMessageBox.warning(self, "Error", "No preset selected.")

    def open_create_preset(self):
        """Create new preset"""
        _dialog = CreatePreset(self, title="Create new default preset")
        _dialog.open()

    def open_preset_transfer(self):
        """Transfer preset"""
        _dialog = PresetTransfer(self)
        _dialog.open()

    @staticmethod
    def toggle_autoload(checked: bool):
        """Toggle auto load preset"""
        cfg.application["enable_auto_load_preset"] = checked
        cfg.save(cfg_type=ConfigType.CONFIG)

    def open_context_menu(self, position: QPoint):
        """Open context menu"""
        if not self.listbox_preset.itemAt(position):
            return

        selected_index = self.listbox_preset.currentRow()
        selected_preset_name = self.listbox_preset.item(selected_index).text()
        selected_filename = f"{selected_preset_name}{FileExt.JSON}"
        is_locked = (selected_filename in cfg.user.filelock)

        # Create context menu
        menu = QMenu()  # no parent for temp menu
        menu.addAction("Unlock Preset" if is_locked else "Lock Preset")
        menu.addSeparator()

        menu_class = QMenu()
        menu_class.setTitle("Set Primary for Class")
        for class_name in cfg.user.classes:
            menu_class.addAction(class_name)
        menu.addMenu(menu_class)

        menu.addAction("Clear Primary Tag")
        menu.addSeparator()
        menu.addAction("Duplicate")
        if not is_locked:
            menu.addAction("Rename")
            menu.addAction("Delete")

        selected_action = menu.exec_(self.listbox_preset.mapToGlobal(position))
        if not selected_action:
            return
        action = selected_action.text()

        # Set primary preset Class
        if action in cfg.user.classes:
            cfg.user.classes[action]["preset"] = selected_preset_name
            cfg.save(cfg_type=ConfigType.CLASSES)
        # Clear primary preset tag
        elif action == "Clear Primary Tag":
            for class_name, class_data in cfg.user.classes.items():
                if selected_preset_name == class_data["preset"]:
                    class_data["preset"] = ""
                    cfg.save(cfg_type=ConfigType.CLASSES)
        # Lock/unlock preset
        elif action == "Lock Preset":
            msg_text = (
                f"Lock <b>{selected_filename}</b> preset?<br><br>"
                "Changes to locked preset will not be saved."
            )
            if self.confirm_operation(title="Lock Preset", message=msg_text):
                cfg.user.filelock[selected_filename] = {"version": VERSION}
                cfg.save(cfg_type=ConfigType.FILELOCK)
        elif action == "Unlock Preset":
            msg_text = f"Unlock <b>{selected_filename}</b> preset?"
            if self.confirm_operation(title="Unlock Preset", message=msg_text):
                if cfg.user.filelock.pop(selected_filename, None):
                    cfg.save(cfg_type=ConfigType.FILELOCK)
        # Duplicate preset
        elif action == "Duplicate":
            _dialog = CreatePreset(
                self,
                title="Duplicate Preset",
                mode="duplicate",
                source_filename=selected_filename
            )
            _dialog.open()
        # Rename preset
        elif action == "Rename":
            _dialog = CreatePreset(
                self,
                title="Rename Preset",
                mode="rename",
                source_filename=selected_filename
            )
            _dialog.open()
        # Delete preset
        elif action == "Delete":
            msg_text = (
                f"Delete <b>{selected_filename}</b> preset permanently?<br><br>"
                "This cannot be undone!"
            )
            if self.confirm_operation(title="Delete Preset", message=msg_text):
                if os.path.exists(f"{cfg.path.settings}{selected_filename}"):
                    os.remove(f"{cfg.path.settings}{selected_filename}")
        # Refresh
        app_signal.refresh.emit(True)

    def confirm_operation(self, title: str = "Confirm", message: str = "") -> bool:
        """Confirm operation"""
        confirm = QMessageBox.question(
            self, title, message,
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        return confirm == QMessageBox.Yes


class CreatePreset(BaseDialog):
    """Create preset"""

    def __init__(self, parent, title: str = "", mode: str = "", source_filename: str = ""):
        """Initialize create preset dialog setting

        Args:
            title: Dialog title string.
            mode: Edit mode, either "duplicate", "rename", or "" for new preset.
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
        # Rename preset
        elif self.edit_mode == "rename":
            os.rename(
                f"{filepath}{source_filename}",
                f"{filepath}{entered_filename}{FileExt.JSON}"
            )
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


class PresetTagItem(QWidget):
    """Preset tag item"""

    def __init__(self, parent, preset_name: str):
        super().__init__(parent)
        layout_item = QHBoxLayout()
        layout_item.setContentsMargins(0, 0, 0, 0)
        layout_item.setSpacing(0)
        layout_item.addStretch(1)

        # Class name tag
        for class_name, class_data in cfg.user.classes.items():
            if preset_name == class_data["preset"]:
                label_class_name = QLabel(class_name)
                label_class_name.setStyleSheet(f"background: {class_data['color']};")
                layout_item.addWidget(label_class_name)

        # File lock tag
        preset_filename = f"{preset_name}{FileExt.JSON}"
        if preset_filename in cfg.user.filelock:
            label_locked = QLabel(f"{cfg.user.filelock[preset_filename]['version']}")
            label_locked.setStyleSheet("background: #777;")
            layout_item.addWidget(label_locked)

        self.setLayout(layout_item)
