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
Menu
"""

import os

from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QMenu, QMessageBox

from .. import loader
from ..api_control import API_PACK, api
from ..const_app import URL_FAQ, URL_USER_GUIDE
from ..const_file import ConfigType
from ..module_info import minfo
from ..overlay_control import octrl
from ..setting import cfg
from ..update import update_checker
from .about import About
from .brake_editor import BrakeEditor
from .config import FontConfig, UserConfig
from .driver_stats_viewer import DriverStatsViewer
from .fuel_calculator import FuelCalculator
from .heatmap_editor import HeatmapEditor
from .log_info import LogInfo
from .track_info_editor import TrackInfoEditor
from .track_map_viewer import TrackMapViewer
from .track_notes_editor import TrackNotesEditor
from .tyre_compound_editor import TyreCompoundEditor
from .vehicle_brand_editor import VehicleBrandEditor
from .vehicle_class_editor import VehicleClassEditor


class OverlayMenu(QMenu):
    """Overlay menu, shared between main & tray menu"""

    def __init__(self, title, parent, is_tray: bool = False):
        super().__init__(title, parent)
        if is_tray:
            self.loaded_preset = self.addAction("")
            self.loaded_preset.setDisabled(True)
            self.aboutToShow.connect(self.refresh_preset_name)
            self.addSeparator()

        # Lock overlay
        self.overlay_lock = self.addAction("Lock Overlay")
        self.overlay_lock.setCheckable(True)
        self.overlay_lock.triggered.connect(self.is_locked)

        # Auto hide
        self.overlay_hide = self.addAction("Auto Hide")
        self.overlay_hide.setCheckable(True)
        self.overlay_hide.triggered.connect(self.is_hidden)

        # Grid move
        self.overlay_grid = self.addAction("Grid Move")
        self.overlay_grid.setCheckable(True)
        self.overlay_grid.triggered.connect(self.has_grid)

        # VR Compatbiility
        self.overlay_vr = self.addAction("VR Compatibility")
        self.overlay_vr.setCheckable(True)
        self.overlay_vr.triggered.connect(self.vr_compatibility)

        # Reload preset
        reload_preset = self.addAction("Reload")
        reload_preset.triggered.connect(parent.reload_preset)
        self.addSeparator()

        # Reset submenu
        menu_reset_data = ResetDataMenu("Reset Data", parent)
        self.addMenu(menu_reset_data)
        self.addSeparator()

        # Config
        if is_tray:
            app_config = self.addAction("Config")
            app_config.triggered.connect(parent.show_app)
            self.addSeparator()

        # Quit
        app_quit = self.addAction("Quit")
        app_quit.triggered.connect(parent.quit_app)

        # Refresh menu
        self.aboutToShow.connect(self.refresh_menu)

    def refresh_menu(self):
        """Refresh menu"""
        self.overlay_lock.setChecked(cfg.overlay["fixed_position"])
        self.overlay_hide.setChecked(cfg.overlay["auto_hide"])
        self.overlay_grid.setChecked(cfg.overlay["enable_grid_move"])
        self.overlay_vr.setChecked(cfg.overlay["vr_compatibility"])

    def refresh_preset_name(self):
        """Refresh preset name"""
        loaded_preset = cfg.filename.setting[:-5]
        if len(loaded_preset) > 16:
            loaded_preset = f"{loaded_preset[:16]}..."
        self.loaded_preset.setText(loaded_preset)

    @staticmethod
    def is_locked():
        """Check lock state"""
        octrl.toggle.lock()

    @staticmethod
    def is_hidden():
        """Check hide state"""
        octrl.toggle.hide()

    @staticmethod
    def has_grid():
        """Check grid move state"""
        octrl.toggle.grid()

    @staticmethod
    def vr_compatibility():
        """Check VR compatibility state"""
        octrl.toggle.vr()


class ResetDataMenu(QMenu):
    """Reset user data menu"""

    def __init__(self, title, parent):
        super().__init__(title, parent)
        self._parent = parent

        reset_deltabest = self.addAction("Delta Best")
        reset_deltabest.triggered.connect(self.reset_deltabest)

        reset_energydelta = self.addAction("Energy Delta")
        reset_energydelta.triggered.connect(self.reset_energydelta)

        reset_fueldelta = self.addAction("Fuel Delta")
        reset_fueldelta.triggered.connect(self.reset_fueldelta)

        reset_consumption = self.addAction("Consumption History")
        reset_consumption.triggered.connect(self.reset_consumption)

        reset_sectorbest = self.addAction("Sector Best")
        reset_sectorbest.triggered.connect(self.reset_sectorbest)

        reset_trackmap = self.addAction("Track Map")
        reset_trackmap.triggered.connect(self.reset_trackmap)

    def reset_deltabest(self):
        """Reset deltabest data"""
        self.__confirmation(
            data_type="delta best",
            extension="csv",
            filepath=cfg.path.delta_best,
            filename=api.read.session.combo_name(),
        )

    def reset_energydelta(self):
        """Reset energy delta data"""
        self.__confirmation(
            data_type="energy delta",
            extension="energy",
            filepath=cfg.path.energy_delta,
            filename=api.read.session.combo_name(),
        )

    def reset_fueldelta(self):
        """Reset fuel delta data"""
        self.__confirmation(
            data_type="fuel delta",
            extension="fuel",
            filepath=cfg.path.fuel_delta,
            filename=api.read.session.combo_name(),
        )

    def reset_consumption(self):
        """Reset consumption history data"""
        if self.__confirmation(
            data_type="consumption history",
            extension="consumption",
            filepath=cfg.path.fuel_delta,
            filename=api.read.session.combo_name(),
        ):
            minfo.history.reset_consumption()

    def reset_sectorbest(self):
        """Reset sector best data"""
        self.__confirmation(
            data_type="sector best",
            extension="sector",
            filepath=cfg.path.sector_best,
            filename=api.read.session.combo_name(),
        )

    def reset_trackmap(self):
        """Reset trackmap data"""
        self.__confirmation(
            data_type="track map",
            extension="svg",
            filepath=cfg.path.track_map,
            filename=api.read.session.track_name(),
        )

    def __confirmation(self, data_type: str, extension: str, filepath: str, filename: str) -> bool:
        """Message confirmation, returns true if file deleted"""
        # Check if on track
        if api.read.state.active():
            QMessageBox.warning(
                self._parent,
                "Error",
                "Cannot reset data while on track.",
            )
            return False
        # Check if file exist
        filename_full = f"{filepath}{filename}.{extension}"
        if not os.path.exists(filename_full):
            QMessageBox.warning(
                self._parent,
                "Error",
                f"No {data_type} data found.<br><br>You can only reset data from active session.",
            )
            return False
        # Confirm reset
        msg_text = (
            f"Reset <b>{data_type}</b> data for<br>"
            f"<b>{filename}</b> ?<br><br>"
            "This cannot be undone!"
        )
        delete_msg = QMessageBox.question(
            self._parent, f"Reset {data_type.title()}", msg_text,
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if delete_msg != QMessageBox.Yes:
            return False
        # Delete file
        os.remove(filename_full)
        QMessageBox.information(
            self._parent,
            f"Reset {data_type.title()}",
            f"{data_type.capitalize()} data has been reset for<br><b>{filename}</b>",
        )
        return True


class ConfigMenu(QMenu):
    """Config menu"""

    def __init__(self, title, parent):
        super().__init__(title, parent)
        self._parent = parent

        config_app = self.addAction("Application")
        config_app.triggered.connect(self.open_config_application)

        config_compat = self.addAction("Compatibility")
        config_compat.triggered.connect(self.open_config_compatibility)

        config_userpath = self.addAction("User Path")
        config_userpath.triggered.connect(self.open_config_userpath)
        self.addSeparator()

        config_units = self.addAction("Units")
        config_units.triggered.connect(self.open_config_units)

        config_font = self.addAction("Global Font Override")
        config_font.triggered.connect(self.open_config_font)

    def open_config_application(self):
        """Config global application"""
        _dialog = UserConfig(
            parent=self._parent,
            key_name="application",
            cfg_type=ConfigType.CONFIG,
            user_setting=cfg.user.config,
            default_setting=cfg.default.config,
            reload_func=self._parent.reload_preset,
        )
        _dialog.open()

    def open_config_compatibility(self):
        """Config global compatibility"""
        _dialog = UserConfig(
            parent=self._parent,
            key_name="compatibility",
            cfg_type=ConfigType.CONFIG,
            user_setting=cfg.user.config,
            default_setting=cfg.default.config,
            reload_func=self._parent.reload_preset,
        )
        _dialog.open()

    def open_config_userpath(self):
        """Config global user path"""
        _dialog = UserConfig(
            parent=self._parent,
            key_name="user_path",
            cfg_type=ConfigType.CONFIG,
            user_setting=cfg.user.config,
            default_setting=cfg.default.config,
            reload_func=self._parent.reload_preset,
            option_width=22,
        )
        _dialog.open()

    def open_config_font(self):
        """Config global font"""
        _dialog = FontConfig(
            parent=self._parent,
            user_setting=cfg.user.setting,
            reload_func=self._parent.reload_only,
        )
        _dialog.open()

    def open_config_units(self):
        """Config display units"""
        _dialog = UserConfig(
            parent=self._parent,
            key_name="units",
            cfg_type=ConfigType.SETTING,
            user_setting=cfg.user.setting,
            default_setting=cfg.default.setting,
            reload_func=self._parent.reload_only,
        )
        _dialog.open()


class APIMenu(QMenu):
    """API menu"""

    def __init__(self, title, parent):
        super().__init__(title, parent)
        self._parent = parent

        # API selector
        self.actions_api = self.__api_selector()
        self.addSeparator()

        self.api_selection = self.addAction("Remember API Selection from Preset")
        self.api_selection.setCheckable(True)
        self.api_selection.triggered.connect(self.toggle_api_selection)

        config_api = self.addAction("Options")
        config_api.triggered.connect(self.open_config_api)
        self.addSeparator()

        restart_api = self.addAction("Restart API")
        restart_api.triggered.connect(parent.restart_api)

        self.aboutToShow.connect(self.refresh_menu)

    def refresh_menu(self):
        """Refresh menu"""
        selected_api_name = cfg.api_name
        for action in self.actions_api.actions():
            if selected_api_name == action.text():
                action.setChecked(True)
                break
        self.api_selection.setChecked(cfg.telemetry["enable_api_selection_from_preset"])

    def toggle_api_selection(self):
        """Toggle API selection mode"""
        enabled = cfg.telemetry["enable_api_selection_from_preset"]
        cfg.telemetry["enable_api_selection_from_preset"] = not enabled
        cfg.save(cfg_type=ConfigType.CONFIG)
        self._parent.reload_only()

    def open_config_api(self):
        """Config API"""
        _dialog = UserConfig(
            parent=self._parent,
            key_name=cfg.api_key,
            cfg_type=ConfigType.SETTING,
            user_setting=cfg.user.setting,
            default_setting=cfg.default.setting,
            reload_func=self._parent.restart_api,
        )
        _dialog.open()

    def __api_selector(self):
        """Generate API selector"""
        if os.getenv("PYSIDE_OVERRIDE") == "6":
            from PySide6.QtGui import QActionGroup
        else:
            from PySide2.QtWidgets import QActionGroup

        actions_api = QActionGroup(self)

        for _api in API_PACK:
            api_name = _api.NAME
            option = self.addAction(api_name)
            option.setCheckable(True)
            option.triggered.connect(lambda checked=True, name=api_name: self.__toggle_option(checked, name))
            actions_api.addAction(option)
        return actions_api

    def __toggle_option(self, checked: bool, api_name: str):
        """Toggle option"""
        if cfg.api_name == api_name:
            return
        cfg.api_name = api_name
        if cfg.telemetry["enable_api_selection_from_preset"]:
            save_type = ConfigType.SETTING
        else:
            save_type = ConfigType.CONFIG
        cfg.save(cfg_type=save_type)
        self._parent.reload_only()


class ToolsMenu(QMenu):
    """Tools menu"""

    def __init__(self, title, parent):
        super().__init__(title, parent)
        self._parent = parent

        utility_fuelcalc = self.addAction("Fuel Calculator")
        utility_fuelcalc.triggered.connect(self.open_utility_fuelcalc)

        utility_driverstats = self.addAction("Driver Stats Viewer")
        utility_driverstats.triggered.connect(self.open_utility_driverstats)

        utility_mapviewer = self.addAction("Track Map Viewer")
        utility_mapviewer.triggered.connect(self.open_utility_mapviewer)
        self.addSeparator()

        editor_heatmap = self.addAction("Heatmap Editor")
        editor_heatmap.triggered.connect(self.open_editor_heatmap)

        editor_brakes = self.addAction("Brake Editor")
        editor_brakes.triggered.connect(self.open_editor_brakes)

        editor_compounds = self.addAction("Tyre Compound Editor")
        editor_compounds.triggered.connect(self.open_editor_compounds)

        editor_brands = self.addAction("Vehicle Brand Editor")
        editor_brands.triggered.connect(self.open_editor_brands)

        editor_classes = self.addAction("Vehicle Class Editor")
        editor_classes.triggered.connect(self.open_editor_classes)

        editor_trackinfo = self.addAction("Track Info Editor")
        editor_trackinfo.triggered.connect(self.open_editor_trackinfo)

        editor_tracknotes = self.addAction("Track Notes Editor")
        editor_tracknotes.triggered.connect(self.open_editor_tracknotes)

    def open_utility_fuelcalc(self):
        """Fuel calculator"""
        _dialog = FuelCalculator(self._parent)
        _dialog.show()

    def open_utility_driverstats(self):
        """Track driver stats viewer"""
        _dialog = DriverStatsViewer(self._parent)
        _dialog.show()

    def open_utility_mapviewer(self):
        """Track map viewer"""
        _dialog = TrackMapViewer(self._parent)
        _dialog.show()

    def open_editor_heatmap(self):
        """Edit heatmap preset"""
        _dialog = HeatmapEditor(self._parent)
        _dialog.show()

    def open_editor_brakes(self):
        """Edit brakes preset"""
        _dialog = BrakeEditor(self._parent)
        _dialog.show()

    def open_editor_compounds(self):
        """Edit compounds preset"""
        _dialog = TyreCompoundEditor(self._parent)
        _dialog.show()

    def open_editor_brands(self):
        """Edit brands preset"""
        _dialog = VehicleBrandEditor(self._parent)
        _dialog.show()

    def open_editor_classes(self):
        """Edit classes preset"""
        _dialog = VehicleClassEditor(self._parent)
        _dialog.show()

    def open_editor_trackinfo(self):
        """Edit track info"""
        _dialog = TrackInfoEditor(self._parent)
        _dialog.show()

    def open_editor_tracknotes(self):
        """Edit track notes"""
        _dialog = TrackNotesEditor(self._parent)
        _dialog.show()


class WindowMenu(QMenu):
    """Window menu"""

    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.show_at_startup = self.addAction("Show at Startup")
        self.show_at_startup.setCheckable(True)
        self.show_at_startup.triggered.connect(self.is_show_at_startup)

        self.minimize_to_tray = self.addAction("Minimize to Tray")
        self.minimize_to_tray.setCheckable(True)
        self.minimize_to_tray.triggered.connect(self.is_minimize_to_tray)

        self.remember_position = self.addAction("Remember Position")
        self.remember_position.setCheckable(True)
        self.remember_position.triggered.connect(self.is_remember_position)

        self.remember_size = self.addAction("Remember Size")
        self.remember_size.setCheckable(True)
        self.remember_size.triggered.connect(self.is_remember_size)
        self.addSeparator()

        restart_app = self.addAction("Restart TinyPedal")
        restart_app.triggered.connect(loader.restart)

        self.aboutToShow.connect(self.refresh_menu)

    def refresh_menu(self):
        """Refresh menu"""
        self.show_at_startup.setChecked(cfg.application["show_at_startup"])
        self.minimize_to_tray.setChecked(cfg.application["minimize_to_tray"])
        self.remember_position.setChecked(cfg.application["remember_position"])
        self.remember_size.setChecked(cfg.application["remember_size"])

    def is_show_at_startup(self):
        """Toggle config window startup state"""
        self.__toggle_option("show_at_startup")

    def is_minimize_to_tray(self):
        """Toggle minimize to tray state"""
        self.__toggle_option("minimize_to_tray")

    def is_remember_position(self):
        """Toggle config window remember position state"""
        self.__toggle_option("remember_position")

    def is_remember_size(self):
        """Toggle config window remember size state"""
        self.__toggle_option("remember_size")

    @staticmethod
    def __toggle_option(option_name: str):
        """Toggle option"""
        cfg.application[option_name] = not cfg.application[option_name]
        cfg.save(cfg_type=ConfigType.CONFIG)


class HelpMenu(QMenu):
    """Help menu"""

    def __init__(self, title, parent):
        super().__init__(title, parent)
        self._parent = parent

        app_guide = self.addAction("User Guide")
        app_guide.triggered.connect(self.open_user_guide)

        app_faq = self.addAction("FAQ")
        app_faq.triggered.connect(self.open_faq)

        app_log = self.addAction("Show Log")
        app_log.triggered.connect(self.show_log)
        self.addSeparator()

        app_update = self.addAction("Check for Updates")
        app_update.triggered.connect(self.show_update)
        self.addSeparator()

        app_about = self.addAction("About")
        app_about.triggered.connect(self.show_about)

    def show_about(self):
        """Show about"""
        _dialog = About(self._parent)
        _dialog.show()

    def show_log(self):
        """Show log"""
        _dialog = LogInfo(self._parent)
        _dialog.show()

    def show_update(self):
        """Show update"""
        update_checker.check(True)

    def open_user_guide(self):
        """Open user guide link"""
        QDesktopServices.openUrl(URL_USER_GUIDE)

    def open_faq(self):
        """Open FAQ link"""
        QDesktopServices.openUrl(URL_FAQ)
