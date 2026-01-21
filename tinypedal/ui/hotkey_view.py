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
Hotkey list view
"""

from typing import Callable

from PySide2.QtCore import QBasicTimer, Qt, Slot
from PySide2.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..const_app import PLATFORM
from ..const_file import ConfigType
from ..formatter import format_option_name
from ..hotkey.common import (
    format_hotkey_name,
    get_key_state_function,
    modifier_priority,
    refresh_keystate,
)
from ..hotkey.keymap import KEYMAP_GENERAL, KEYMAP_MODIFIER
from ..hotkey_control import kctrl
from ..setting import cfg
from ._common import BaseDialog, UIScaler


class HotkeyList(QWidget):
    """Hotkey list view"""

    def __init__(self, parent, notify_toggle: Callable):
        """Initialize hotkey list setting"""
        super().__init__(parent)
        self.notify_toggle = notify_toggle
        self.last_enabled = None

        # List box
        self.listbox_hotkey = QListWidget(self)
        self.listbox_hotkey.setAlternatingRowColors(True)
        self.create_list()

        # Button
        self.button_reset = QPushButton("Clear All")
        self.button_reset.clicked.connect(self.reset_hotkey)

        self.button_toggle = QPushButton("")
        self.button_toggle.setCheckable(True)
        self.button_toggle.toggled.connect(self.toggle_hotkey)
        self.refresh()

        # Layout
        layout_main = QVBoxLayout()
        layout_button = QHBoxLayout()
        layout_button.addWidget(self.button_reset)
        layout_button.addStretch(1)
        layout_button.addWidget(self.button_toggle)
        layout_main.addWidget(self.listbox_hotkey)
        layout_main.addLayout(layout_button)
        margin = UIScaler.pixel(6)
        layout_main.setContentsMargins(margin, margin, margin, margin)
        self.setLayout(layout_main)

    def set_button_state(self, enabled: bool):
        """Set button state"""
        self.button_toggle.setChecked(enabled)
        self.button_toggle.setText("Enabled" if enabled else "Disabled")
        self.button_reset.setDisabled(not enabled)
        self.listbox_hotkey.setDisabled(not enabled)
        self.notify_toggle(enabled)

    def toggle_hotkey(self, checked: bool):
        """Toggle hotkey mode"""
        cfg.application["enable_global_hotkey"] = checked
        cfg.save(cfg_type=ConfigType.CONFIG)
        kctrl.reload()
        self.refresh()

    def create_list(self):
        """Create hotkey option list"""
        for option_name in cfg.user.shortcuts:
            module_item = HotkeyConfigItem(self, option_name)
            item = QListWidgetItem()
            item.setText(format_option_name(option_name))
            self.listbox_hotkey.addItem(item)
            self.listbox_hotkey.setItemWidget(item, module_item)
        self.listbox_hotkey.setCurrentRow(0)

    @Slot(bool)  # type: ignore[operator]
    def refresh(self):
        """Refresh hotkey list"""
        enabled = cfg.application["enable_global_hotkey"]
        # Update button state only if changed
        if self.last_enabled != enabled:
            self.last_enabled = enabled
            self.set_button_state(enabled)

    def reset_hotkey(self):
        """Reset hotkey"""
        msg_text = "Clear all key bindings?<br><br>This cannot be undone!"
        confirm_msg = QMessageBox.question(
            self, "Confirm", msg_text,
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if confirm_msg == QMessageBox.Yes:
            # Clear all shortcuts
            for options in cfg.user.shortcuts.values():
                options["bind"] = ""
            cfg.save(0, cfg_type=ConfigType.SHORTCUTS)
            # Refresh button
            listbox_hotkey = self.listbox_hotkey
            for row_index in range(listbox_hotkey.count()):
                item = listbox_hotkey.itemWidget(listbox_hotkey.item(row_index))
                item.reload_hotkey()
            # Reload
            kctrl.reload()


class HotkeyConfigItem(QWidget):
    """Hotkey configuration item"""

    def __init__(self, parent, option_name: str):
        super().__init__(parent)
        self._parent = parent
        self.option_name = option_name
        self.hotkey_name = ""

        self.button_config = QPushButton("")
        self.button_config.setCheckable(True)
        self.button_config.clicked.connect(self.open_config_dialog)

        self.reload_hotkey()

        layout_item = QHBoxLayout()
        layout_item.setContentsMargins(0, 0, 0, 0)
        layout_item.addStretch(1)
        layout_item.setSpacing(0)
        layout_item.addWidget(self.button_config)
        self.setLayout(layout_item)

    def open_config_dialog(self):
        """Config dialog"""
        kctrl.disable()  # disable before config
        self.button_config.setChecked(False)
        _dialog = ConfigHotkey(
            self._parent,
            option_name=self.option_name,
            hotkey_name=self.hotkey_name,
            reload_func=self.reload_hotkey,
        )
        _dialog.open()

    def reload_hotkey(self):
        """Reload button state"""
        if cfg.application["enable_global_hotkey"]:
            kctrl.enable()  # re-enable after config
        self.hotkey_name = cfg.user.shortcuts[self.option_name]["bind"]
        display_name = format_hotkey_name(self.hotkey_name, "None")
        self.button_config.setText(f" {display_name} " if len(display_name) < 2 else display_name)
        self.button_config.setChecked(self.hotkey_name != "")


class ConfigHotkey(BaseDialog):
    """Configure hotkey dialog"""

    def __init__(self, parent, option_name: str, hotkey_name: str, reload_func: Callable):
        super().__init__(parent)
        self.option_name = option_name
        self.hotkey_name = hotkey_name
        self.temp_hotkey = hotkey_name
        self.reloading = reload_func

        self.setWindowTitle(f"Key Binding - {format_option_name(self.option_name)}")

        # Entry box
        self.hotkey_entry = QLineEdit()
        self.hotkey_entry.setReadOnly(True)
        self.hotkey_entry.setAlignment(Qt.AlignCenter)

        # Button
        button_clear = QPushButton("Clear")
        button_clear.clicked.connect(self.reset)

        button_confirm = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_confirm.accepted.connect(self.accept)
        button_confirm.rejected.connect(self.reject)

        # Layout
        layout_main = QVBoxLayout()
        layout_button = QHBoxLayout()
        layout_button.addWidget(button_clear)
        layout_button.addWidget(button_confirm)
        layout_main.addWidget(self.hotkey_entry)
        layout_main.addLayout(layout_button)
        self.setLayout(layout_main)
        self.setMinimumWidth(UIScaler.size(21))
        self.setFixedHeight(self.sizeHint().height())

        # Set update timer
        self._update_timer = QBasicTimer()

        # Platform specific
        self.get_key_state = get_key_state_function()
        refresh_keystate(self.get_key_state)

        if PLATFORM == "Windows":
            self.text_placeholder = "Press a key or key combination"
            self.update_text(format_hotkey_name(hotkey_name, self.text_placeholder, delimiter=" + "))
            self._update_timer.start(200, self)
        else:
            self.text_placeholder = "Hotkey not supported on Linux"
            self.update_text(self.text_placeholder)

    def timerEvent(self, event):
        """Monitor key press"""
        if PLATFORM == "Windows":
            self.monitor_key_win(KEYMAP_GENERAL, KEYMAP_MODIFIER)

    def monitor_key_win(self, key_general, key_modifier):
        """Monitor key press - Windows"""
        key_combo = [""] * 4  # Ctrl, Alt, Shift, Key
        is_combo_set = False

        # Key state: 0=off, 1=pressed, <1=down
        # Assign mod key
        for key, code in key_modifier.items():
            priority = modifier_priority(key)
            if self.get_key_state(code) != 0:
                key_combo[priority] = key
            else:  # remove if not pressed
                key_combo[priority] = ""
        # Assign common key
        for key, code in key_general.items():
            if self.get_key_state(code) != 0:
                key_combo[-1] = key
                is_combo_set = True
                break

        if is_combo_set:
            hotkey_name = "+".join(_key for _key in key_combo if _key)
            self.temp_hotkey = hotkey_name
            self.update_text(format_hotkey_name(hotkey_name, delimiter=" + "))
            refresh_keystate(self.get_key_state)

    def reset(self):
        """Reset hotkey"""
        self.temp_hotkey = ""
        self.update_text(self.text_placeholder)

    def update_text(self, text: str):
        """Update entry text"""
        self.hotkey_entry.setText(text)

    def accept(self):
        """Saving hotkey"""
        if self.temp_hotkey != self.hotkey_name:
            # Check for duplicated hotkey
            for option_name, options in cfg.user.shortcuts.items():
                other_hotkey = options["bind"]
                if "" != other_hotkey == self.temp_hotkey:
                    msg_text = (
                        f"<b>{format_hotkey_name(self.temp_hotkey)}</b> already used for """
                        f"<b>{format_option_name(option_name)}</b>.<br><br>"
                        "Please set a different hotkey."
                    )
                    QMessageBox.warning(self, "Error", msg_text)
                    return

            cfg.user.shortcuts[self.option_name]["bind"] = self.temp_hotkey
            cfg.save(0, cfg_type=ConfigType.SHORTCUTS)
        self.close()

    def reject(self):
        """Reject(ESC)"""
        self.close()

    def closeEvent(self, event):
        """Close dialog"""
        self._update_timer.stop()
        self.reloading()
        self.get_key_state = None
        self.reloading = None
