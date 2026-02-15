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
Overlay base window, events.
"""

from __future__ import annotations

import logging
from typing import Any

from PySide2.QtCore import QBasicTimer, Qt, Slot
from PySide2.QtGui import QFont, QFontMetrics, QPalette, QPixmap
from PySide2.QtWidgets import QGridLayout, QLayout, QMenu, QWidget

from .. import app_signal, overlay_signal, realtime_state
from ..const_app import APP_NAME
from ..formatter import format_module_name
from ..regex_pattern import FONT_WEIGHT_MAP
from ..setting import Setting
from ._common import FontMetrics, MousePosition
from ._painter import RawImage, RawText

logger = logging.getLogger(__name__)
mousepos = MousePosition()  # single instance shared by all widgets


class Base(QWidget):
    """Base window"""

    def __init__(self, config: Setting, widget_name: str):
        super().__init__()
        self.widget_name = widget_name

        # Base config
        self.cfg = config

        # Widget config
        self.wcfg = validate_option(self.cfg.user.setting[widget_name])

        # Base setting
        self.setWindowTitle(f"{APP_NAME} - {widget_name.capitalize()}")
        self.move(self.wcfg["position_x"], self.wcfg["position_y"])

        # Set update timer
        self._update_timer = QBasicTimer()
        self._update_interval = max(
            self.wcfg["update_interval"],
            self.cfg.application["minimum_update_interval"],
        )

    def start(self):
        """Set initial widget state in orders, and start update"""
        self.__connect_signal()
        self.__set_window_attributes()  # 1
        self.__set_window_flags()  # 2
        self.__toggle_timer(not realtime_state.active)

    def stop(self):
        """Stop and close widget"""
        self.__toggle_timer(True)
        self.__break_signal()
        self.__unload_resource()
        if not self.close():
            logger.error(
                "FAILED TO CLOSE: widget %s",
                self._overlay.widget_name,
            )

    @property
    def closed(self) -> bool:
        """Close state"""
        return self.cfg is None and self.close()

    def post_update(self):
        """Run once after state inactive"""

    def __unload_resource(self):
        """Unload widget resource"""
        for var in self.__dict__:
            setattr(self, var, None)

    def __set_window_attributes(self):
        """Set window attributes"""
        self.setWindowOpacity(self.wcfg["opacity"])
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if self.cfg.compatibility["enable_translucent_background"]:
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        else:
            self.__set_window_style()

    def __set_window_flags(self):
        """Set window flags"""
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        if not self.cfg.overlay["vr_compatibility"]:  # hide taskbar widget
            self.setWindowFlag(Qt.Tool, True)
        if self.cfg.compatibility["enable_bypass_window_manager"]:
            self.setWindowFlag(Qt.X11BypassWindowManagerHint, True)
        self.__toggle_lock(locked=self.cfg.overlay["fixed_position"])

    def __set_window_style(self):
        """Set window style"""
        palette = self.palette()
        palette.setColor(QPalette.Window, self.cfg.compatibility["global_bkg_color"])
        self.setPalette(palette)

    def __save_position(self):
        """Save widget position"""
        save_changes = False
        if self.wcfg["position_x"] != self.x():
            self.wcfg["position_x"] = self.x()
            save_changes = True
        if self.wcfg["position_y"] != self.y():
            self.wcfg["position_y"] = self.y()
            save_changes = True
        if save_changes:
            self.cfg.save()

    @Slot(bool)  # type: ignore[operator]
    def __toggle_lock(self, locked: bool):
        """Toggle widget lock state"""
        self.setWindowFlag(Qt.WindowTransparentForInput, locked)
        # Need re-check after lock/unlock
        self.setHidden(self.cfg.overlay["auto_hide"] and not realtime_state.active)

    @Slot(bool)  # type: ignore[operator]
    def __toggle_vr_compat(self, enabled: bool):
        """Toggle widget VR compatibility"""
        self.setWindowFlag(Qt.Tool, not enabled)
        # Need re-check
        self.setHidden(self.cfg.overlay["auto_hide"] and not realtime_state.active)

    @Slot(bool)  # type: ignore[operator]
    def __toggle_timer(self, paused: bool):
        """Toggle widget timer state"""
        if paused:
            self._update_timer.stop()
            self.post_update()
        else:
            self._update_timer.start(self._update_interval, self)

    def __connect_signal(self):
        """Connect overlay lock and hide signal"""
        overlay_signal.locked.connect(self.__toggle_lock)
        overlay_signal.hidden.connect(self.setHidden)
        overlay_signal.paused.connect(self.__toggle_timer)
        overlay_signal.iconify.connect(self.__toggle_vr_compat)

    def __break_signal(self):
        """Disconnect overlay lock and hide signal"""
        overlay_signal.locked.disconnect(self.__toggle_lock)
        overlay_signal.hidden.disconnect(self.setHidden)
        overlay_signal.paused.disconnect(self.__toggle_timer)
        overlay_signal.iconify.disconnect(self.__toggle_vr_compat)

    def mouseMoveEvent(self, event):
        """Update widget position"""
        if mousepos.valid() and event.buttons() == Qt.LeftButton:
            # Snapping to reference grid if Ctrl is pressed
            if (event.modifiers() & Qt.ControlModifier):
                self.move(mousepos.snapping(self, event.globalPos()))
            else:
                self.move(mousepos.moving(event.globalPos()))

    def mousePressEvent(self, event):
        """Set offset position & press state"""
        # Certain situation or platform can bypass "WindowTransparentForInput" flag
        # Make sure overlay cannot be dragged while "fixed_position" enabled
        if not self.cfg.overlay["fixed_position"] and event.buttons() == Qt.LeftButton:
            mousepos.config(
                event.pos(),
                self.cfg.overlay["enable_grid_move"],
                self.cfg.application["grid_move_size"],
                self.cfg.application["snap_gap"],
                self.cfg.application["snap_distance"],
            )

    def mouseReleaseEvent(self, event):
        """Save position on release"""
        mousepos.reset()
        self.__save_position()

    def contextMenuEvent(self, event):
        """Widget context menu"""
        menu = QMenu()

        show_name = menu.addAction(format_module_name(self.widget_name))
        show_name_font = show_name.font()
        show_name_font.setBold(True)
        show_name.setFont(show_name_font)
        menu.addSeparator()

        menu.addAction("Config")
        menu.addSeparator()
        menu.addAction("Center Horizontally")
        menu.addAction("Center Vertically")
        menu.addSeparator()
        menu.addAction("Reload")
        menu.addAction("Disable")

        selected_action = menu.exec_(event.globalPos())
        if not selected_action:
            return

        action = selected_action.text()
        if action == "Center Horizontally":
            self.move((self.screen().geometry().width() - self.width()) // 2, self.y())
            self.__save_position()
        elif action == "Center Vertically":
            self.move(self.x(), (self.screen().geometry().height() - self.height()) // 2)
            self.__save_position()
        elif action == "Config":
            config_widget(self.widget_name)
        elif action == "Reload":
            reload_widget(self.widget_name)
        elif action == "Disable":
            disable_widget(self.widget_name)

    def closeEvent(self, event):
        """Ignore attempts to close via window Close button when VR compatibility enabled"""
        if self.cfg is not None:
            event.ignore()


class Overlay(Base):
    """Inherit base window, add common GUI methods"""

    def config_font(self, name: str = "", size: int | float = 1, weight: str = "") -> QFont:
        """Config font

        Used for draw text in widget that uses QPainter,
        or get font metrics reading for sizing elements.

        Args:
            name: font name string.
            size: font size in pixel, minimum limit 1px.
            weight (optional): font weight name string, convert name to capital.

        Returns:
            QFont object.
        """
        font = self.font()  # get existing widget font
        font.setFamily(name)
        font.setPixelSize(max(int(size), 1))
        if weight:
            font.setWeight(FONT_WEIGHT_MAP[weight])
        return font

    def get_font_metrics(self, font: QFont) -> FontMetrics:
        """Get font metrics

        Args:
            font: QFont object.

        Returns:
            FontMetrics object.
        """
        # Disable font hinting for more accuracy (necessary for pyside6)
        font.setHintingPreference(QFont.PreferNoHinting)
        font_metrics = QFontMetrics(font)
        return FontMetrics(
            width=font_metrics.averageCharWidth(),
            height=font_metrics.height(),
            leading=font_metrics.leading(),
            capital=font_metrics.capHeight(),
            descent=font_metrics.descent(),
            voffset=self.__calc_font_offset(font_metrics),
        )

    def __calc_font_offset(self, metrics: QFontMetrics) -> int:
        """Calculate auto font vertical offset

        Find difference between actual height and height reading
        and use as offset for center vertical alignment position
        for overlay that uses QPainter drawing.

        Args:
            metrics: FontMetrics object.

        Returns:
            Calculated font offset in pixel.
        """
        if self.wcfg["enable_auto_font_offset"]:
            return (
                metrics.capHeight()
                + metrics.descent() * 2
                + metrics.leading() * 2
                - metrics.height()
            )
        return self.wcfg["font_offset_vertical"]

    @staticmethod
    def set_padding(size: int, scale: float, side: int = 2) -> int:
        """Set padding

        Args:
            size: reference font size in pixel.
            scale: scale font size for relative padding.
            side: number of sides to add padding.

        Returns:
            Padding size in pixel.
        """
        return round(size * scale) * side

    @staticmethod
    def set_text_alignment(align: int | str = 0) -> Qt.Alignment:
        """Set text alignment

        Args:
            align: 0 or "Center", 1 or "Left", 2 or "Right".

        Returns:
            Qt alignment.
        """
        if align == 0 or align == "Center":
            return Qt.AlignCenter
        if align == 1 or align == "Left":
            return Qt.AlignLeft | Qt.AlignVCenter
        return Qt.AlignRight | Qt.AlignVCenter

    def set_rawtext(
        self,
        *,
        font: QFont | None = None,
        text: str = "",
        width: int = 0,
        height: int = 0,
        fixed_width: int = 0,
        fixed_height: int = 0,
        offset_y: int = 0,
        fg_color: str = "",
        bg_color: str = "",
        alignment: Qt.Alignment = Qt.AlignCenter,
        last: Any | None = None,
        count: int = 1,
    ) -> tuple[RawText, ...] | RawText:
        """Set RawText, keyword arguments only

        Args:
            font: QFont.
            text: bar text.
            width: fixed width in pixel.
            height: fixed height in pixel.
            fixed_width: fixed width in pixel, takes priority over width.
            fixed_height: fixed height in pixel, takes priority over height.
            offset_y: font vertical offset in pixel.
            fg_color: foreground (font) color.
            bg_color: background color.
            alignment: Qt.Alignment.
            last: cache last data for comparison.
            count: number of RawText to set.

        Returns:
            A single or multiple(tuple) RawText instances,
            depends on count value (default 1).
        """
        bar_set = (
            RawText(
                parent=self,
                font=font,
                width=width,
                height=height,
                fixed_width=fixed_width,
                fixed_height=fixed_height,
                offset_y=offset_y,
                fg_color=fg_color,
                bg_color=bg_color,
                text=text,
                alignment=alignment,
                last=last,
            )
            for _ in range(count)
        )
        if count > 1:
            return tuple(bar_set)
        return next(bar_set)

    def set_rawimage(
        self,
        *,
        image: QPixmap | None = None,
        width: int = 0,
        height: int = 0,
        fixed_width: int = 0,
        fixed_height: int = 0,
        bg_color: str = "",
        last: Any | None = None,
        count: int = 1,
    ) -> tuple[RawImage, ...] | RawImage:
        """Set RawImage, keyword arguments only

        Args:
            image: QPixmap image.
            width: fixed width in pixel.
            height: fixed height in pixel.
            fixed_width: fixed width in pixel, takes priority over width.
            fixed_height: fixed height in pixel, takes priority over height.
            bg_color: background color.
            last: cache last data for comparison.
            count: number of RawImage to set.

        Returns:
            A single or multiple(tuple) RawImage instances,
            depends on count value (default 1).
        """
        bar_set = (
            RawImage(
                parent=self,
                image=image,
                width=width,
                height=height,
                fixed_width=fixed_width,
                fixed_height=fixed_height,
                bg_color=bg_color,
                last=last,
            )
            for _ in range(count)
        )
        if count > 1:
            return tuple(bar_set)
        return next(bar_set)

    @staticmethod
    def set_grid_layout_vert(
        layout: QGridLayout,
        targets: tuple[QWidget, ...],
        row_start: int = 1,
        column: int = 4,
    ):
        """Set grid layout - vertical

        Default row index start from 1; reserve row index 0 for caption.
        """
        for index, target in enumerate(targets):
            layout.addWidget(target, index + row_start, column)

    @staticmethod
    def set_grid_layout_quad(
        layout: QGridLayout,
        targets: tuple[QWidget | QLayout, ...],
        row_start: int = 1,
        column_left: int = 0,
        column_right: int = 9,
    ):
        """Set grid layout - quad - (0,1), (2,3), (4,5), ...

        Default row index start from 1; reserve row index 0 for caption.
        """
        for index, target in enumerate(targets):
            row_index = row_start + (index // 2)
            column_index = column_left + (index % 2) * column_right
            if isinstance(target, QWidget):
                layout.addWidget(target, row_index, column_index)
            else:
                layout.addLayout(target, row_index, column_index)

    @staticmethod
    def set_grid_layout_table_row(
        layout: QGridLayout,
        targets: tuple[QWidget, ...],
        row_index: int = 0,
        right_to_left: bool = False,
        hide_start: int = 99999,
    ):
        """Set grid layout - table by keys of each row"""
        if right_to_left:
            enum_target = enumerate(reversed(targets))
        else:
            enum_target = enumerate(targets)
        for column_index, target in enum_target:
            layout.addWidget(target, row_index, column_index)
            if hide_start <= column_index:
                target.hide()

    @staticmethod
    def set_grid_layout_table_column(
        layout: QGridLayout,
        targets: tuple[QWidget, ...],
        column_index: int = 0,
        bottom_to_top: bool = False,
        hide_start: int = 99999,
    ):
        """Set grid layout - table by keys of each column"""
        if bottom_to_top:
            enum_target = enumerate(reversed(targets))
        else:
            enum_target = enumerate(targets)
        for row_index, target in enum_target:
            layout.addWidget(target, row_index, column_index)
            if hide_start <= row_index:
                target.hide()

    @staticmethod
    def set_grid_layout(
        gap: int = 0,
        gap_hori: int = -1,
        gap_vert: int = -1,
        margin: int = -1,
        align: Qt.Alignment | None = None,
    ) -> QGridLayout:
        """Set grid layout (QGridLayout)"""
        layout = QGridLayout()
        layout.setSpacing(gap)
        if gap_hori >= 0:
            layout.setHorizontalSpacing(gap_hori)
        if gap_vert >= 0:
            layout.setVerticalSpacing(gap_vert)
        if margin >= 0:
            layout.setContentsMargins(margin, margin, margin, margin)
        if align is not None:
            layout.setAlignment(align)
        return layout

    def set_primary_layout(
        self,
        layout: QLayout,
        margin: int = 0,
        align: Qt.Alignment | None = Qt.AlignLeft | Qt.AlignTop,
    ):
        """Set primary layout"""
        layout.setContentsMargins(margin, margin, margin, margin)
        if align is not None:
            layout.setAlignment(align)
        self.setLayout(layout)

    def set_primary_orient(
        self,
        target: QWidget | QGridLayout,
        column: int = 0,
        row: int = 0,
        option: str = "layout",
        default: str | int = 0,
    ):
        """Set primary layout (QGridLayout) orientation

        Orientation is defined by "layout" option in Widget JSON.
        0 = vertical, 1 = horizontal.

        Args:
            target: QWidget or QGridLayout that adds to primary layout.
            column: column index determines display order.
            row: row index determines side display order.
            option: layout option name in Widget JSON.
            default: default layout value.
        """
        layout = self.layout()
        assert isinstance(layout, QGridLayout)
        if self.wcfg.get(option, 0) == default:
            order = column, row  # Vertical layout
        else:
            order = row, column  # Horizontal layout
        if isinstance(target, QWidget):
            layout.addWidget(target, *order)
        else:
            layout.addLayout(target, *order)


def validate_option(config: dict) -> dict:
    """Post validation for options"""
    # Check column/row index order, correct any overlapping indexes
    column_set = []
    for key in config:
        if key.startswith("column_index"):
            while config[key] in column_set:
                config[key] += 1
            column_set.append(config[key])
    return config


def disable_widget(widget_name: str):
    """Disable widget"""
    from ..module_control import wctrl
    wctrl.toggle(widget_name)
    app_signal.refresh.emit(True)


def reload_widget(widget_name: str):
    """Reload widget"""
    from ..module_control import wctrl
    wctrl.reload(widget_name)
    app_signal.refresh.emit(True)


def config_widget(widget_name: str):
    """Open widget config dialog"""
    from PySide2.QtWidgets import QApplication, QMainWindow

    from ..module_control import wctrl
    from ..setting import cfg
    from ..ui.config import UserConfig

    # Find main window instance
    for _widget in QApplication.topLevelWidgets():
        if isinstance(_widget, QMainWindow):
            break
    else:
        return
    _dialog = UserConfig(
        parent=_widget,
        key_name=widget_name,
        cfg_type=wctrl.type_id,
        user_setting=cfg.user.setting,
        default_setting=cfg.default.setting,
        reload_func=lambda name=widget_name: reload_widget(name),
    )
    _dialog.open()
