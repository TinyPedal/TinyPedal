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
Main application window
"""

import logging
import time

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import app_signal, loader
from ..api_control import api
from ..const_api import API_MAP_ALIAS
from ..const_app import APP_NAME, VERSION
from ..const_file import ConfigType
from ..module_control import mctrl, wctrl
from ..setting import cfg
from . import set_style_palette, set_style_window
from ._common import UIScaler
from .hotkey_view import HotkeyList
from .menu import APIMenu, ConfigMenu, HelpMenu, OverlayMenu, ToolsMenu, WindowMenu
from .module_view import ModuleList
from .notification import NotifyBar
from .pace_notes_view import PaceNotesControl
from .preset_view import PresetList
from .spectate_view import SpectateList

logger = logging.getLogger(__name__)


class TabView(QWidget):
    """Tab view"""

    def __init__(self, parent):
        super().__init__(parent)
        # Notify bar
        notify_bar = NotifyBar(self)

        notify_bar.presetlocked.clicked.connect(self.select_preset_tab)
        notify_bar.spectate.clicked.connect(self.select_spectate_tab)
        notify_bar.pacenotes.clicked.connect(self.select_pacenotes_tab)
        notify_bar.hotkey.clicked.connect(self.select_hotkey_tab)

        app_signal.updates.connect(notify_bar.updates.checking)
        app_signal.refresh.connect(notify_bar.refresh)

        # Tabs
        widget_tab = ModuleList(self, wctrl)
        module_tab = ModuleList(self, mctrl)
        preset_tab = PresetList(self, notify_bar.presetlocked.setVisible)
        spectate_tab = SpectateList(self, notify_bar.spectate.setVisible)
        pacenotes_tab = PaceNotesControl(self, notify_bar.pacenotes.setVisible)
        hotkey_tab = HotkeyList(self, notify_bar.hotkey.setVisible)

        app_signal.refresh.connect(widget_tab.refresh)
        app_signal.refresh.connect(module_tab.refresh)
        app_signal.refresh.connect(preset_tab.refresh)
        app_signal.refresh.connect(spectate_tab.refresh)
        app_signal.refresh.connect(pacenotes_tab.refresh)
        app_signal.refresh.connect(hotkey_tab.refresh)

        self._tabs = QTabWidget(self)
        self._tabs.addTab(widget_tab, "Widget")  # 0
        self._tabs.addTab(module_tab, "Module")  # 1
        self._tabs.addTab(preset_tab, "Preset")  # 2
        self._tabs.addTab(spectate_tab, "Spectate")  # 3
        self._tabs.addTab(pacenotes_tab, "Pace Notes")  # 4
        self._tabs.addTab(hotkey_tab, "Hotkey")  # 5

        # Main view
        layout_main = QVBoxLayout()
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.setSpacing(0)
        layout_main.addWidget(self._tabs)
        layout_main.addWidget(notify_bar)
        self.setLayout(layout_main)

    def select_preset_tab(self):
        """Select preset tab"""
        self._tabs.setCurrentIndex(2)

    def select_spectate_tab(self):
        """Select spectate tab"""
        self._tabs.setCurrentIndex(3)

    def select_pacenotes_tab(self):
        """Select pace notes tab"""
        self._tabs.setCurrentIndex(4)

    def select_hotkey_tab(self):
        """Select hotkey tab"""
        self._tabs.setCurrentIndex(5)


class StatusButtonBar(QStatusBar):
    """Status button bar"""

    def __init__(self, parent):
        super().__init__(parent)
        self.button_api = QPushButton("")
        self.button_api.clicked.connect(self.refresh)
        self.button_api.setToolTip("Config Telemetry API")

        self.button_style = QPushButton("")
        self.button_style.clicked.connect(self.toggle_color_theme)
        self.button_style.setToolTip("Toggle Window Color Theme")

        self.button_dpiscale = QPushButton("")
        self.button_dpiscale.clicked.connect(self.toggle_dpi_scaling)
        self.button_dpiscale.setToolTip("Toggle High DPI Scaling")
        self._last_dpi_scaling = cfg.application["enable_high_dpi_scaling"]

        self.addPermanentWidget(self.button_api)
        self.addWidget(self.button_style)
        self.addWidget(self.button_dpiscale)

        app_signal.refresh.connect(self.refresh)

    @Slot(bool)  # type: ignore[operator]
    def refresh(self):
        """Refresh status bar"""
        if cfg.api["enable_active_state_override"]:
            text_api_status = "overriding"
        else:
            text_api_status = api.read.state.version()
        self.button_api.setText(f"API: {API_MAP_ALIAS[api.name]} ({text_api_status})")

        self.button_style.setText(f"UI: {cfg.application['window_color_theme']}")

        if cfg.application["enable_high_dpi_scaling"]:
            text_dpi = "Auto"
        else:
            text_dpi = "Off"
        if self._last_dpi_scaling != cfg.application["enable_high_dpi_scaling"]:
            text_need_restart = "*"
        else:
            text_need_restart = ""
        self.button_dpiscale.setText(f"Scale: {text_dpi}{text_need_restart}")

    def toggle_dpi_scaling(self):
        """Toggle DPI scaling"""
        if cfg.application["enable_high_dpi_scaling"]:
            state = "Disable"
            desc = "not be scaled under high DPI screen resolution."
        else:
            state = "Enable"
            desc = "be auto-scaled according to system DPI scaling setting."
        msg_text = (
            f"{state} <b>High DPI Scaling</b> and restart <b>TinyPedal</b>?<br><br>"
            f"<b>Window</b> and <b>Overlay</b> size and position will {desc}"
        )
        restart_msg = QMessageBox.question(
            self, "High DPI Scaling", msg_text,
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if restart_msg != QMessageBox.Yes:
            return

        cfg.application["enable_high_dpi_scaling"] = not cfg.application["enable_high_dpi_scaling"]
        cfg.save(0, cfg_type=ConfigType.CONFIG)
        # Wait saving finish
        while cfg.is_saving:
            time.sleep(0.01)
        loader.restart()

    def toggle_color_theme(self):
        """Toggle color theme"""
        if cfg.application["window_color_theme"] == "Dark":
            cfg.application["window_color_theme"] = "Light"
        else:
            cfg.application["window_color_theme"] = "Dark"
        cfg.save(cfg_type=ConfigType.CONFIG)
        app_signal.refresh.emit(True)


class AppWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.last_style = None

        # Status bar
        self.setStatusBar(StatusButtonBar(self))

        # Menu bar
        self.set_menu_bar()

        # Tab view
        self.tab_view = TabView(self)
        self.setCentralWidget(self.tab_view)

        # Tray icon
        self.set_tray_icon()

        # Window state
        self.set_window_state()
        self.__connect_signal()

        # Refresh GUI
        self.refresh_only()

    @Slot(bool)  # type: ignore[operator]
    def refresh(self):
        """Refresh GUI"""
        # Window style
        style = cfg.application["window_color_theme"]
        logger.info("GUI: loading window color theme: %s", style)
        if self.last_style != style:
            self.last_style = style
            set_style_palette(self.last_style)
            self.setStyleSheet(set_style_window(QApplication.font().pointSize()))

    def set_menu_bar(self):
        """Set menu bar"""
        logger.info("GUI: loading window menu")
        menu = self.menuBar()
        # Overlay menu
        menu_overlay = OverlayMenu("Overlay", self)
        menu.addMenu(menu_overlay)
        # API menu
        menu_api = APIMenu("API", self)
        menu.addMenu(menu_api)
        self.statusBar().button_api.setMenu(menu_api)
        # Config menu
        menu_config = ConfigMenu("Config", self)
        menu.addMenu(menu_config)
        # Tools menu
        menu_tools = ToolsMenu("Tools", self)
        menu.addMenu(menu_tools)
        # Window menu
        menu_window = WindowMenu("Window", self)
        menu.addMenu(menu_window)
        # Help menu
        menu_help = HelpMenu("Help", self)
        menu.addMenu(menu_help)

    def set_tray_icon(self):
        """Set tray icon"""
        logger.info("GUI: loading tray icon")
        tray_icon = QSystemTrayIcon(self)
        # Config tray icon
        tray_icon.setIcon(self.windowIcon())
        tray_icon.setToolTip(self.windowTitle())
        tray_icon.activated.connect(self.tray_doubleclick)
        # Add tray menu
        tray_menu = OverlayMenu("Overlay", self, True)
        tray_icon.setContextMenu(tray_menu)
        tray_icon.show()

    def tray_doubleclick(self, active_reason: QSystemTrayIcon.ActivationReason):
        """Tray doubleclick"""
        if active_reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_app()

    def set_window_state(self):
        """Set initial window state"""
        self.setMinimumSize(UIScaler.size(23), UIScaler.size(36))
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)  # disable maximize

        if cfg.application["remember_size"]:
            self.resize(
                cfg.application["window_width"],
                cfg.application["window_height"],
            )

        if cfg.application["remember_position"]:
            self.load_window_position()

        if cfg.compatibility["enable_window_position_correction"]:
            self.verify_window_position()

        if cfg.application["show_at_startup"]:
            self.showNormal()
        elif not cfg.application["minimize_to_tray"]:
            self.showMinimized()

    def load_window_position(self):
        """Load window position"""
        logger.info("GUI: loading window setting")
        app_pos_x = cfg.application["position_x"]
        app_pos_y = cfg.application["position_y"]
        # Save new x,y position if preset value at 0,0
        if 0 == app_pos_x == app_pos_y:
            self.save_window_state()
        else:
            self.move(app_pos_x, app_pos_y)

    def verify_window_position(self):
        """Verify window position"""
        # Get screen size from the screen where app window located
        screen_geo = self.screen().geometry()
        # Limiting position value if out of screen range
        app_pos_x = min(
            max(self.x(), screen_geo.left()),
            screen_geo.right() - self.minimumWidth(),
        )
        app_pos_y = min(
            max(self.y(), screen_geo.top()),
            screen_geo.bottom() - self.minimumHeight(),
        )
        # Re-adjust position only if mismatched
        if self.x() != app_pos_x or self.y() != app_pos_y:
            self.move(app_pos_x, app_pos_y)
            logger.info("GUI: window position corrected")

    def save_window_state(self):
        """Save window state"""
        save_changes = False

        if cfg.application["remember_position"]:
            last_pos = cfg.application["position_x"], cfg.application["position_y"]
            new_pos = self.x(), self.y()
            if last_pos != new_pos:
                cfg.application["position_x"] = new_pos[0]
                cfg.application["position_y"] = new_pos[1]
                save_changes = True

        if cfg.application["remember_size"]:
            last_size = cfg.application["window_width"], cfg.application["window_height"]
            new_size = self.width(), self.height()
            if last_size != new_size:
                cfg.application["window_width"] = new_size[0]
                cfg.application["window_height"] = new_size[1]
                save_changes = True

        if save_changes:
            cfg.save(0, cfg_type=ConfigType.CONFIG)

    def show_app(self):
        """Show app window"""
        self.showNormal()
        self.activateWindow()

    @Slot(bool)  # type: ignore[operator]
    def quit_app(self):
        """Quit manager"""
        loader.close()  # must close this first
        self.save_window_state()
        self.__break_signal()
        self.findChild(QSystemTrayIcon).hide()  # workaround tray icon not removed after exited
        QApplication.quit()

    def closeEvent(self, event):
        """Minimize to tray"""
        if cfg.application["minimize_to_tray"]:
            event.ignore()
            self.hide()
        else:
            self.quit_app()

    def restart_api(self):
        """Restart telemetry API"""
        api.restart()
        self.refresh_only()

    @Slot(bool)  # type: ignore[operator]
    def reload_preset(self):
        """Reload current preset"""
        loader.reload(reload_preset=True)
        self.refresh_only()

    def reload_only(self):
        """Reload only api, module, widget"""
        loader.reload(reload_preset=False)
        self.refresh_only()

    def refresh_only(self):
        """Refresh GUI only"""
        app_signal.refresh.emit(True)

    def __connect_signal(self):
        """Connect signal"""
        app_signal.refresh.connect(self.refresh)
        app_signal.quitapp.connect(self.quit_app)
        app_signal.reload.connect(self.reload_preset)
        logger.info("GUI: connect signals")

    def __break_signal(self):
        """Disconnect signal"""
        app_signal.updates.disconnect()
        app_signal.refresh.disconnect()
        app_signal.quitapp.disconnect()
        app_signal.reload.disconnect()
        logger.info("GUI: disconnect signals")
