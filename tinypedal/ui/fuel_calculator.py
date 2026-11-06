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
Fuel calculator
"""

from __future__ import annotations

import os
from collections import deque

from PySide2.QtCore import QPoint, Qt
from PySide2.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PySide2.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import api, cfg, minfo, units
from .. import calculation as calc
from ..constant import CONFIG, DATA, FILE
from ..formatter import laptime_string_to_seconds
from ..module_info import ConsumptionData
from ..userfile.consumption_history import load_consumption_history_file
from ._common import BaseDialog, UIScaler


def _set_layout(layout: QLayout, spacing: int = 2, margin: int = 4):
    """Set layout"""
    spacing = UIScaler.pixel(spacing)
    margin = UIScaler.pixel(margin)
    layout.setSpacing(spacing)
    layout.setContentsMargins(margin, margin, margin, margin)
    return layout


def _highlight_invalid(line_edit: QLineEdit, invalid=False):
    """Highlight invalid"""
    line_edit.setStyleSheet("QLineEdit {background: #F40;}" if invalid else "")


def _add_output(row: int, column: int, layout: QGridLayout, editor: QWidget, title_text: str, unit_text: str):
    """Add output edit"""
    layout.addWidget(QLabel(title_text), row, column, 1, 2)
    layout.addWidget(editor, row + 1, column)
    if unit_text:
        layout.addWidget(QLabel(unit_text), row + 1, column + 1)
    return editor


def _add_data_column(
    key: str,
    name: str,
    width: float,
    process: object,
    flags: Qt.ItemFlag,
    config: str = "",
    highlight: bool = False,
):
    """Add lap data column"""
    return {
        "key": key,
        "name": name,
        "width": width,
        "process": process,
        "flags": flags,
        "config": config,
        "highlight": highlight,
    }


class FuelCalculator(BaseDialog):
    """Fuel calculator"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Fuel Calculator")
        layout_main = QVBoxLayout()
        self.setLayout(layout_main)

        # Set status bar
        self.status_bar = QStatusBar(self)

        # Panel history
        self.panel_history = HistoryPanel(self)

        self.button_adddata = QPushButton("Add Selected Data")
        self.button_adddata.clicked.connect(self.add_selected_data)
        self.button_adddata.setFocusPolicy(Qt.NoFocus)

        layout_history = QVBoxLayout()
        layout_history.addWidget(self.panel_history)
        layout_history.addWidget(self.button_adddata)

        # Panel calculator
        self.panel_calculator = CalculatorPanel(self)

        button_loadlive = QPushButton("Load Live")
        button_loadlive.clicked.connect(self.load_live_data)
        button_loadlive.setFocusPolicy(Qt.NoFocus)

        button_loadfile = QPushButton("Load File")
        button_loadfile.clicked.connect(self.load_file_data)
        button_loadfile.setFocusPolicy(Qt.NoFocus)

        self.button_toggle = QPushButton("Hide History")
        self.button_toggle.setCheckable(True)
        self.button_toggle.setChecked(True)
        self.button_toggle.toggled.connect(self.toggle_history_panel)
        self.button_toggle.setChecked(cfg.user.config["fuel_calculator"]["show_consumption_history"])
        self.button_toggle.setFocusPolicy(Qt.NoFocus)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_loadlive, stretch=1)
        layout_button.addWidget(button_loadfile, stretch=1)
        layout_button.addStretch(1)
        layout_button.addWidget(self.button_toggle, stretch=2)

        layout_calculator = QVBoxLayout()
        layout_calculator.addWidget(self.panel_calculator)
        layout_calculator.addLayout(layout_button)

        # Layout
        layout_panel = QHBoxLayout()
        layout_panel.addLayout(layout_calculator)
        layout_panel.addLayout(layout_history)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, 0)
        layout_main.addLayout(layout_panel, stretch=1)
        layout_main.addWidget(self.status_bar)

        self.toggle_history_panel(cfg.user.config["fuel_calculator"]["show_consumption_history"])
        self.load_live_data()

    def load_file_data(self):
        """Load history data from file"""
        filename_full = QFileDialog.getOpenFileName(
            self,
            dir=cfg.path.fuel_delta,
            filter=";;".join((FILE.FILTER_CONSUMPTION, FILE.FILTER_CSV))
        )[0]
        if not filename_full:
            return

        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.splitext(os.path.basename(filename_full))[0]
        history_data = load_consumption_history_file(
            filepath=filepath,
            filename=filename,
        )
        self.panel_calculator.fill_in_data(history_data)
        self.panel_history.refresh(history_data)
        self.status_bar.showMessage(f"File Source: {filename}")

    def load_live_data(self):
        """Load history data from live session"""
        history_data = minfo.history.consumptionDataSet
        self.panel_calculator.fill_in_data(history_data)
        self.panel_history.refresh(history_data)
        self.status_bar.showMessage(f"Live Source: {api.read.session.combo_name()}")

    def add_selected_data(self):
        """Add selected data to calculator"""
        selected_data = self.panel_history.table_history.selectedItems()
        if not selected_data:
            QMessageBox.warning(self, "Error", "No data selected.")
            return
        self.panel_calculator.add_table_data(selected_data)

    def toggle_history_panel(self, checked: bool):
        """Toggle history data panel"""
        self.panel_history.setHidden(not checked)
        self.button_adddata.setHidden(not checked)
        self.button_toggle.setText("Hide History" if checked else "Show History")

        margin = self.layout().contentsMargins()
        width = self.panel_calculator.width() + margin.left() + margin.right()

        if checked:
            width += self.panel_history.sizeHint().width() + self.layout().spacing()
        self.setFixedWidth(width)

        config = cfg.user.config["fuel_calculator"]
        if config["show_consumption_history"] != checked:
            config["show_consumption_history"] = checked
            cfg.save(config_type=CONFIG.TYPE_CONFIG)

    def table_header_menu(self, position: QPoint):
        """Open table header context menu"""
        config = cfg.user.config["fuel_calculator"]
        table = self.panel_history.table_history

        menu = QMenu()  # no parent for temp menu

        for option_name in config:
            if option_name.startswith("show_column"):
                action_name = option_name.replace("show_column_", "").replace("_", " ").title()
                action = menu.addAction(action_name)
                action.setCheckable(True)
                action.setChecked(config[option_name])

        selected_action = menu.exec_(table.mapToGlobal(position))
        if not selected_action:
            return

        selected_name = "show_column_" + selected_action.text().replace(" ", "_").lower()
        if selected_name in config:
            config[selected_name] = not config[selected_name]
            self.panel_history.toggle_column()
            self.toggle_history_panel(config["show_consumption_history"])
            cfg.save(config_type=CONFIG.TYPE_CONFIG)


class PitStopPreview(QWidget):
    """Pit stop preview"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(UIScaler.size(2.2))
        self.floor_total_laps = 0
        self.floor_stint_runlaps = 0
        self.floor_start_runlaps = 0

        frame = QFrame(self)
        frame.setFrameShape(QFrame.StyledPanel)

        self.label_laps = QLabel(DATA.TEXT_PLACEHOLDER)
        self.label_laps.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(frame, stretch=1)
        layout.addWidget(self.label_laps)
        self.setLayout(layout)

    def sync(self, total_laps: float, stint_runlaps: float, start_runlaps: float):
        """Sync data"""
        self.floor_total_laps = int(total_laps)
        self.floor_stint_runlaps = int(stint_runlaps)
        self.floor_start_runlaps = int(start_runlaps) if start_runlaps > 0 else self.floor_stint_runlaps
        self.label_laps.setText(str(self.floor_total_laps) if self.floor_total_laps else DATA.TEXT_PLACEHOLDER)
        self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        length = self.height()
        width = self.width()
        palette = self.palette()

        # Background
        painter.fillRect(0, 0, width, length, palette.base().color())

        # Marks
        floor_total_laps = self.floor_total_laps
        floor_stint_runlaps = self.floor_stint_runlaps
        floor_start_runlaps = self.floor_start_runlaps
        if floor_total_laps > 0 < floor_stint_runlaps:

            length -= self.label_laps.height()

            # Lap mark
            laps = 1
            lap_color = palette.mid().color()
            while laps < floor_total_laps:
                lap_mark_y = laps / floor_total_laps * length
                if lap_mark_y < 5:
                    break
                painter.fillRect(0, lap_mark_y, width, 1, lap_color)
                laps += 1

            # Pit mark
            pit_count = 1
            pit_text_height = self.fontMetrics().height() * 2
            pit_color = palette.highlight().color()
            laps = floor_start_runlaps
            while laps < floor_total_laps:
                pit_mark_y = laps / floor_total_laps * length - 3
                painter.fillRect(0, pit_mark_y, width, 6, pit_color)
                painter.drawText(
                    0, pit_mark_y - pit_text_height, width, pit_text_height,
                    Qt.AlignHCenter | Qt.AlignBottom,
                    f"{laps}",
                )
                pit_count += 1
                laps = floor_start_runlaps + floor_stint_runlaps * (pit_count - 1)


class HistoryPanel(QWidget):
    """History data panel"""

    def __init__(self, parent):
        super().__init__(parent)
        # Set (freeze) fuel unit
        self.unit_fuel = units.set_unit_fuel(cfg.units["fuel_unit"])
        self.symbol_fuel = units.set_symbol_fuel(cfg.units["fuel_unit"])

        flag_selectable = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        flag_unselectable = Qt.ItemIsEnabled
        self.columns = (
            _add_data_column(
                key="lap",
                name="Lap",
                width=3,
                process=(lambda data: f"{data.lapNumber}" if data.lapNumber > 0 else DATA.TEXT_PLACEHOLDER),
                flags=flag_unselectable,
            ),
            _add_data_column(
                key="stint",
                name="Stint",
                width=3,
                process=(lambda data: f"{data.stintLapNumber}" if data.stintLapNumber > 0 else DATA.TEXT_PLACEHOLDER),
                flags=flag_unselectable,
                config="show_column_stint_laps",
            ),
            _add_data_column(
                key="time",
                name="Time",
                width=6,
                process=(lambda data: calc.sec2laptime_full(data.lapTimeLast)),
                flags=flag_selectable,
                highlight=True,
            ),
            _add_data_column(
                key="fuel",
                name=f"Fuel({self.symbol_fuel})",
                width=5,
                process=(lambda data: f"{self.unit_fuel(data.lastLapUsedFuel):.3f}"),
                flags=flag_selectable,
                highlight=True,
            ),
            _add_data_column(
                key="energy",
                name="NRG(%)",
                width=5,
                process=(lambda data: f"{data.lastLapUsedEnergy:.3f}"),
                flags=flag_selectable,
                highlight=True,
            ),
            _add_data_column(
                key="ratio",
                name="F/Ratio",
                width=5,
                process=(lambda data: f"{calc.fuel_to_energy_ratio(data.lastLapUsedFuel, data.lastLapUsedEnergy):.3f}"),
                flags=flag_unselectable,
                config="show_column_fuel_ratio",
            ),
            _add_data_column(
                key="drain",
                name="Drain(%)",
                width=5,
                process=(lambda data: f"{data.batteryDrainLast:.3f}"),
                flags=flag_unselectable,
                config="show_column_battery_drain",
            ),
            _add_data_column(
                key="regen",
                name="Regen(%)",
                width=5,
                process=(lambda data: f"{data.batteryRegenLast:.3f}"),
                flags=flag_unselectable,
                config="show_column_battery_regen",
            ),
            _add_data_column(
                key="net",
                name="B/Net(%)",
                width=5,
                process=(lambda data: f"{data.batteryRegenLast - data.batteryDrainLast:+.3f}"),
                flags=flag_unselectable,
                config="show_column_battery_net_change",
            ),
            _add_data_column(
                key="tyre_wear",
                name="Tyre F(%)",
                width=5,
                process=(lambda data: f"{max(data.tyreWearFL, data.tyreWearFR):.3f}"),
                flags=flag_selectable,
                config="show_column_tyre_wear_front",
            ),
            _add_data_column(
                key="tyre_wear",
                name="Tyre R(%)",
                width=5,
                process=(lambda data: f"{max(data.tyreWearRL, data.tyreWearRR):.3f}"),
                flags=flag_selectable,
                config="show_column_tyre_wear_rear",
            ),
            _add_data_column(
                key="brake_wear",
                name="Pad F(mm)",
                width=6,
                process=(lambda data: f"{max(data.brakeWearFL, data.brakeWearFR):.6f}"),
                flags=flag_selectable,
                config="show_column_brake_wear_front",
            ),
            _add_data_column(
                key="brake_wear",
                name="Pad R(mm)",
                width=6,
                process=(lambda data: f"{max(data.brakeWearRL, data.brakeWearRR):.6f}"),
                flags=flag_selectable,
                config="show_column_brake_wear_rear",
            ),
            _add_data_column(
                key="tank",
                name=f"Tank({self.symbol_fuel})",
                width=5,
                process=(lambda data: f"{self.unit_fuel(data.capacityFuel):.3f}"),
                flags=flag_selectable,
                config="show_column_tank_capacity",
            ),
        )

        self.table_history = QTableWidget(self)
        self.table_history.setColumnCount(len(self.columns))
        self.table_history.setHorizontalHeaderLabels([col["name"] for col in self.columns])
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        for idx, col in enumerate(self.columns):
            self.table_history.setColumnWidth(idx, UIScaler.size(col["width"]))

        table_hori_header = self.table_history.horizontalHeader()
        table_hori_header.setSectionResizeMode(QHeaderView.Fixed)
        table_hori_header.setStretchLastSection(True)
        table_hori_header.setContextMenuPolicy(Qt.CustomContextMenu)
        table_hori_header.customContextMenuRequested.connect(parent.table_header_menu)
        self.toggle_column()

        layout_panel = QVBoxLayout()
        layout_panel.setContentsMargins(0, 0, 0, 0)
        layout_panel.addWidget(self.table_history)
        self.setLayout(layout_panel)

    def toggle_column(self):
        """Toggle column visibility"""
        config = cfg.user.config["fuel_calculator"]
        table = self.table_history

        width = self.table_history.verticalScrollBar().sizeHint().width() + 3
        for idx, col in enumerate(self.columns):
            if col["config"]:
                table.setColumnHidden(idx, not config[col["config"]])
            if not table.isColumnHidden(idx):
                width += UIScaler.size(col["width"])

        table.setFixedWidth(width)

    def refresh(self, dataset: deque[ConsumptionData]):
        """Refresh history data table"""
        table = self.table_history
        table.setRowCount(0)
        invalid_color = QColor("#F40")
        separator_color = None
        separator_stint = None
        separator_session = None
        lap_number = DATA.MAX_LAPS

        for row_index, lap_data in enumerate(dataset):
            if lap_data.lapNumber > lap_number:  # new session
                separator_color = separator_session
            if lap_data.isValidLap:
                highlight_color = None
            else:
                highlight_color = invalid_color
            # Add row
            table.insertRow(row_index)
            for column_index, col in enumerate(self.columns):
                item = self._add_table_item(
                    key=col["key"],
                    text=col["process"](lap_data),
                    flags=col["flags"],
                    highlight=highlight_color if col["highlight"] else None,
                    background=separator_color,
                )
                table.setItem(row_index, column_index, item)
            # Set separator style
            if row_index == 0:  # get row height after item added to first row
                lin_grad = QLinearGradient(0, 0, 0, table.rowHeight(0))
                lin_grad.setStops(((0.04, "#888"), (0.05, Qt.transparent)))
                separator_stint = QBrush(lin_grad)
                lin_grad.setStops(((0.06, "#F40"), (0.07, Qt.transparent)))
                separator_session = QBrush(lin_grad)
            # Draw line separator on next row
            lap_number = lap_data.lapNumber
            if lap_data.stintLapNumber == 1:  # new stint
                separator_color = separator_stint
            else:
                separator_color = None

    def _add_table_item(self, key: str, text: str, flags: Qt.ItemFlags, highlight=None, background=None):
        """Add table item"""
        item = QTableWidgetItem()
        item.column_key = key
        item.setText(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(flags)
        if highlight:
            item.setForeground(highlight)
        if background:
            item.setBackground(background)
        return item


class CalculatorPanel(QWidget):
    """Calculator data panel"""

    def __init__(self, parent):
        super().__init__(parent)
        # Set (freeze) fuel unit
        self.is_gallon = cfg.units["fuel_unit"] == "Gallon"
        self.unit_fuel = units.set_unit_fuel(cfg.units["fuel_unit"])
        self.symbol_fuel = units.set_symbol_fuel(cfg.units["fuel_unit"])

        # Set preview
        self.pit_preview = PitStopPreview(self)

        self.input_laptime = InputLapTime(self)
        self.input_fuel = InputFuel(self)
        self.input_race = InputRace(self)

        self.usage_fuel = OutputUsage(self, "Fuel")
        self.usage_energy = OutputUsage(self, "Energy")

        self.input_tyre = InputWear(self, "Tyre")
        self.input_brake = InputWear(self, "Pad")

        # Fuel usage tab
        panel_result = QFrame()
        layout_result = _set_layout(QHBoxLayout(), 4)
        layout_result.addWidget(self.usage_fuel)
        layout_result.addWidget(self.usage_energy)
        layout_result.setAlignment(Qt.AlignTop)
        panel_result.setLayout(layout_result)

        # Wear rate tab
        panel_wear = QFrame()
        layout_wear = _set_layout(QVBoxLayout(), 4)
        layout_wear.addWidget(self.input_tyre)
        layout_wear.addWidget(self.input_brake)
        layout_wear.setAlignment(Qt.AlignTop)
        panel_wear.setLayout(layout_wear)

        # Result tabs
        result_tabs = QTabWidget(self)
        result_tabs.addTab(panel_result, "Fuel Usage")  # 0
        result_tabs.addTab(panel_wear, "Wear Rate")  # 1

        # Calculator panel
        layout_calculator = QVBoxLayout()
        layout_calculator.setAlignment(Qt.AlignTop)
        layout_calculator.addWidget(self.input_laptime)
        layout_calculator.addWidget(self.input_fuel)
        layout_calculator.addWidget(self.input_race)
        layout_calculator.addWidget(result_tabs)

        layout_panel = QHBoxLayout()
        layout_panel.setContentsMargins(0, 0, 0, 0)
        layout_panel.addWidget(self.pit_preview)
        layout_panel.addLayout(layout_calculator)
        self.setLayout(layout_panel)
        self.setFixedWidth(self.sizeHint().width() * 0.9)

    def fill_in_data(self, dataset: deque[ConsumptionData]):
        """Fill in history data to edit"""
        latest_history = dataset[0]
        # Load laptime from last valid lap
        laptime = latest_history.lapTimeLast
        if laptime > 0 and latest_history.isValidLap:
            self.input_laptime.minutes.setValue(laptime // 60)
            self.input_laptime.seconds.setValue(laptime % 60)
            self.input_laptime.mseconds.setValue(laptime % 1 * 1000)
        # Load tank capacity
        capacity = max(api.read.engine.tank_capacity(), latest_history.capacityFuel)
        if capacity:
            self.input_fuel.capacity.setValue(self.unit_fuel(capacity))
        # Load consumption from last valid lap
        if latest_history.isValidLap:
            # Fuel
            fuel_used = latest_history.lastLapUsedFuel
            self.input_fuel.fuel_used.setValue(self.unit_fuel(fuel_used))
            # Energy
            energy_used = latest_history.lastLapUsedEnergy
            self.input_fuel.energy_used.setValue(energy_used)
            # Tyre wear
            tyre_wear = max(latest_history.tyre_wear())
            self.input_tyre.wear_lap.setValue(tyre_wear)
            # Brake wear
            brake_wear = max(latest_history.brake_wear())
            self.input_brake.wear_millimeter.setValue(brake_wear)

    def add_table_data(self, selected_data: list[QTableWidgetItem]):
        """Add selected history data"""
        data_laptime = []
        data_fuel = []
        data_energy = []
        data_tyrewear = []
        data_brakewear = []
        data_capacity = []

        for data in selected_data:
            column_key = data.column_key
            if column_key == "time":
                data_laptime.append(laptime_string_to_seconds(data.text()))
            elif column_key == "fuel":
                data_fuel.append(float(data.text()))
            elif column_key == "energy":
                data_energy.append(float(data.text()))
            elif column_key == "tyre_wear":
                data_tyrewear.append(float(data.text()))
            elif column_key == "brake_wear":
                data_brakewear.append(float(data.text()))
            elif column_key == "tank":
                data_capacity.append(data)

        # Send data to calculator
        if data_laptime:
            output_value = calc.dataset_mean(data_laptime)
            self.input_laptime.minutes.setValue(output_value // 60)
            self.input_laptime.seconds.setValue(output_value % 60)
            self.input_laptime.mseconds.setValue(output_value % 1 * 1000)
        if data_fuel:
            output_value = calc.dataset_mean(data_fuel)
            self.input_fuel.fuel_used.setValue(output_value)
        if data_energy:
            output_value = calc.dataset_mean(data_energy)
            self.input_fuel.energy_used.setValue(output_value)
        if data_tyrewear:
            output_value = calc.dataset_mean(data_tyrewear)
            self.input_tyre.wear_lap.setValue(output_value)
        if data_brakewear:
            output_value = calc.dataset_mean(data_brakewear)
            self.input_brake.wear_millimeter.setValue(output_value)
        if data_capacity:
            output_value = float(data_capacity[0].text())
            self.input_fuel.capacity.setValue(output_value)

    def update_input(self):
        """Calculate and output results"""
        # Get lap time setup
        self.input_laptime.carry_over()
        laptime = self.input_laptime.to_seconds()

        # Get race setup
        total_race_seconds = self.input_race.minutes.value() * 60
        absolute_race_laps = self.input_race.laps.value()
        total_formation_laps = self.input_race.formation.value()
        average_pit_seconds = self.input_race.pit_seconds.value()

        # Get fuel setup
        tank_capacity = self.input_fuel.capacity.value()
        fuel_used = self.input_fuel.fuel_used.value()
        fuel_start = self.input_fuel.fuel_start.value(
            ) if self.input_fuel.fuel_start.value() else tank_capacity
        energy_used = self.input_fuel.energy_used.value()
        energy_start = self.input_fuel.energy_start.value(
            ) if self.input_fuel.energy_start.value() else 100

        # Calc fuel ratio
        if self.is_gallon:
            fuel_ratio = calc.fuel_to_energy_ratio(fuel_used * 3.785411784, energy_used)
        else:
            fuel_ratio = calc.fuel_to_energy_ratio(fuel_used, energy_used)
        self.input_fuel.fuel_ratio.setText(f"{fuel_ratio:.3f}")

        # Calc fuel
        fuel_total_runlaps, fuel_stint_runlaps, fuel_start_runlaps = self._calc_consumption(
            "fuel", tank_capacity, fuel_used, fuel_start, total_race_seconds,
            absolute_race_laps, total_formation_laps, average_pit_seconds, laptime)

        # Calc energy
        energy_total_runlaps, energy_stint_runlaps, energy_start_runlaps = self._calc_consumption(
            "energy", 100, energy_used, energy_start, total_race_seconds,
            absolute_race_laps, total_formation_laps, average_pit_seconds, laptime)

        # Update pit preview
        if energy_used > 0:
            self.pit_preview.sync(energy_total_runlaps, energy_stint_runlaps, energy_start_runlaps)
        else:
            self.pit_preview.sync(fuel_total_runlaps, fuel_stint_runlaps, fuel_start_runlaps)

        # Calc wear
        # Pick the least runnable laps if both energy & fuel available
        if energy_stint_runlaps > 0 < fuel_stint_runlaps:
            min_stint_runlaps = min(fuel_stint_runlaps, energy_stint_runlaps)
        else:
            min_stint_runlaps = fuel_stint_runlaps
        self.input_tyre.update(min_stint_runlaps, laptime)
        self.input_brake.update(min_stint_runlaps, laptime)

    def _calc_consumption(
        self,
        output_type: str,
        tank_capacity: float,
        consumption: float,
        fuel_start: float,
        total_race_seconds: float,
        absolute_race_laps: int,
        total_formation_laps: float,
        average_pit_seconds: float,
        laptime: float,
    ):
        """Calculate and output results"""
        estimate_pit_counts = 0
        minimum_pit_counts = 0  # minimum pit stop required to finish race
        loop_counts = 10  # max loop limit

        start_runlaps = calc.end_stint_laps(fuel_start, consumption)

        # Total pit seconds depends on estimated pit counts
        # Recalculate and find nearest minimum pit counts on previous loop
        while loop_counts:
            minimum_pit_counts = calc.ceil(estimate_pit_counts)
            if consumption <= 0:  # unavailable
                total_race_laps = 0
            elif total_race_seconds:  # time-type race
                total_pit_seconds = minimum_pit_counts * average_pit_seconds
                total_race_laps = total_formation_laps + calc.time_type_full_laps_remain(
                    laptime, total_race_seconds - total_pit_seconds)
            else:  # lap-type race
                total_race_laps = total_formation_laps + absolute_race_laps

            total_need_frac = calc.total_fuel_needed(total_race_laps, consumption, 0)

            # Keep 1 decimal place for Gallon
            if self.is_gallon and output_type == "fuel":
                total_need_full = calc.ceil(total_need_frac * 10) / 10
            else:
                total_need_full = calc.ceil(total_need_frac)

            # amount_refuel = total_need_full - tank_capacity
            amount_refuel = total_need_full - fuel_start

            amount_curr = min(total_need_full, tank_capacity)

            end_stint_fuel = calc.end_stint_fuel(amount_curr, 0, consumption)

            estimate_pit_counts = calc.end_stint_pit_counts(
                amount_refuel, tank_capacity - end_stint_fuel)

            loop_counts -= 1
            # Set one last loop to revert back to last minimum pit counts
            # If new rounded up minimum pit counts is not enough to finish race
            if (minimum_pit_counts < estimate_pit_counts and
                minimum_pit_counts == int(estimate_pit_counts)):
                loop_counts = 1

            if minimum_pit_counts == calc.ceil(estimate_pit_counts):
                break

        total_runlaps = total_race_laps  # calc.end_stint_laps(total_need_full, consumption)

        total_runmins = calc.end_stint_minutes(total_runlaps, laptime)

        used_one_less = calc.one_less_pit_stop_consumption(
            estimate_pit_counts, tank_capacity, amount_curr, total_runlaps)

        if minimum_pit_counts:
            average_refuel = (
                amount_refuel + minimum_pit_counts * end_stint_fuel
                ) / minimum_pit_counts
        elif fuel_start < total_need_full <= tank_capacity:
            average_refuel = amount_refuel
        else:
            average_refuel = 0

        if total_need_full > tank_capacity:
            stint_runlaps = calc.end_stint_laps(tank_capacity, consumption)
            stint_runmins = calc.end_stint_minutes(stint_runlaps, laptime)
        else:
            stint_runlaps = total_runlaps
            stint_runmins = total_runmins

        # Output
        if output_type == "fuel":
            output_usage = self.usage_fuel
        else:
            output_usage = self.usage_energy

        estimate_pit_counts = max(estimate_pit_counts, 0)
        minimum_pit_counts = max(calc.ceil(minimum_pit_counts), 0)
        final_stint_laps = max(total_runlaps - int(start_runlaps) - int(stint_runlaps) * max(minimum_pit_counts - 1, 0), 0)

        output_usage.total_needed.setText(
            f"{f'{total_need_frac:.3f}':.6} ≈ {total_need_full}")
        output_usage.pit_stops.setText(
            f"{estimate_pit_counts:.3f} ≈ {minimum_pit_counts}")

        output_usage.total_laps.setText(
            f"{total_runlaps:.3f}")
        output_usage.total_minutes.setText(
            f"{total_runmins:.3f}")

        output_usage.stint_laps.setText(
            f"{stint_runlaps:.3f}")
        output_usage.stint_minutes.setText(
            f"{stint_runmins:.3f}")

        output_usage.final_laps.setText(
            f"{final_stint_laps:.3f}")

        output_usage.end_stint.setText(
            f"{end_stint_fuel:.3f}")
        output_usage.one_less_stint.setText(
            f"{max(used_one_less, 0):.3f}")

        output_usage.average_refill.setText(
            f"{average_refuel:.3f}")

        # Set warning color if exceeded tank capacity
        _highlight_invalid(output_usage.average_refill, average_refuel > tank_capacity)
        return total_runlaps, stint_runlaps, start_runlaps


class InputLapTime(QFrame):
    """Input lap time setup"""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        layout = _set_layout(QGridLayout(self))
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(4, 1)

        self.minutes = QSpinBox()
        self.minutes.setAlignment(Qt.AlignRight)
        self.minutes.setRange(0, 9999)
        self.minutes.valueChanged.connect(parent.update_input)

        self.seconds = QSpinBox()
        self.seconds.setAlignment(Qt.AlignRight)
        self.seconds.setRange(-1, 60)
        self.seconds.valueChanged.connect(parent.update_input)

        self.mseconds = QSpinBox()
        self.mseconds.setAlignment(Qt.AlignRight)
        self.mseconds.setRange(-1, 1000)
        self.mseconds.setSingleStep(100)
        self.mseconds.valueChanged.connect(parent.update_input)

        layout.addWidget(QLabel("Lap Time:"), 0, 0, 1, 6)

        layout.addWidget(self.minutes, 1, 0)
        layout.addWidget(QLabel("m"), 1, 1)

        layout.addWidget(self.seconds, 1, 2)
        layout.addWidget(QLabel("s"), 1, 3)

        layout.addWidget(self.mseconds, 1, 4)
        layout.addWidget(QLabel("ms"), 1, 5)

    def to_seconds(self):
        """Output lap time value to seconds"""
        return (
            self.minutes.value() * 60
            + self.seconds.value()
            + self.mseconds.value() * 0.001
        )

    def carry_over(self):
        """Carry over lap time value"""
        if self.seconds.value() > 59:
            self.seconds.setValue(0)
            self.minutes.setValue(self.minutes.value() + 1)
        elif self.seconds.value() < 0:
            if self.minutes.value() > 0:
                self.seconds.setValue(59)
                self.minutes.setValue(self.minutes.value() - 1)
            else:
                self.seconds.setValue(0)

        if self.mseconds.value() > 999:
            self.mseconds.setValue(0)
            self.seconds.setValue(self.seconds.value() + 1)
        elif self.mseconds.value() < 0:
            if self.seconds.value() > 0 or self.minutes.value() > 0:
                self.mseconds.setValue(900)
                self.seconds.setValue(self.seconds.value() - 1)
            else:
                self.mseconds.setValue(0)


class InputFuel(QFrame):
    """Input fuel setup"""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        layout = _set_layout(QGridLayout(self))
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        self.capacity = QDoubleSpinBox()
        self.capacity.setRange(0, 9999)
        self.capacity.setDecimals(3)
        self.capacity.setAlignment(Qt.AlignRight)
        self.capacity.valueChanged.connect(parent.update_input)

        self.fuel_ratio = QLineEdit("0.000")
        self.fuel_ratio.setAlignment(Qt.AlignRight)
        self.fuel_ratio.setReadOnly(True)

        self.fuel_used = QDoubleSpinBox()
        self.fuel_used.setRange(0, 9999)
        self.fuel_used.setDecimals(3)
        self.fuel_used.setSingleStep(0.1)
        self.fuel_used.setAlignment(Qt.AlignRight)
        self.fuel_used.valueChanged.connect(parent.update_input)

        self.energy_used = QDoubleSpinBox()
        self.energy_used.setRange(0, 100)
        self.energy_used.setDecimals(3)
        self.energy_used.setSingleStep(0.1)
        self.energy_used.setAlignment(Qt.AlignRight)
        self.energy_used.valueChanged.connect(parent.update_input)

        self.fuel_start = QDoubleSpinBox()
        self.fuel_start.setDecimals(2)
        self.fuel_start.setAlignment(Qt.AlignRight)
        self.fuel_start.setRange(0, 9999)
        self.fuel_start.valueChanged.connect(parent.update_input)
        self.fuel_start.valueChanged.connect(self.validate_starting_fuel)

        self.energy_start = QDoubleSpinBox()
        self.energy_start.setDecimals(2)
        self.energy_start.setAlignment(Qt.AlignRight)
        self.energy_start.setRange(0, 100)
        self.energy_start.valueChanged.connect(parent.update_input)

        _add_output(0, 0, layout, self.capacity, "Tank Capacity:", parent.symbol_fuel)
        _add_output(0, 2, layout, self.fuel_used, "Fuel Consumption:", parent.symbol_fuel)
        _add_output(2, 0, layout, self.fuel_ratio, "Fuel/Energy Ratio:", "")
        _add_output(2, 2, layout, self.energy_used, "Energy Consumption:", "%")
        _add_output(4, 0, layout, self.fuel_start, "Starting Fuel:", parent.symbol_fuel)
        _add_output(4, 2, layout, self.energy_start, "Starting Energy:", "%")

    def validate_starting_fuel(self, value: float):
        """Validate starting fuel"""
        if value > self.capacity.value():
            self.fuel_start.setValue(self.capacity.value())


class InputRace(QFrame):
    """Input race setup"""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        layout = _set_layout(QGridLayout(self))
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        self.minutes = QSpinBox()
        self.minutes.setRange(0, 9999)
        self.minutes.setAlignment(Qt.AlignRight)
        self.minutes.valueChanged.connect(parent.update_input)
        self.minutes.valueChanged.connect(self.disable_race_lap)

        self.laps = QSpinBox()
        self.laps.setRange(0, 9999)
        self.laps.setAlignment(Qt.AlignRight)
        self.laps.valueChanged.connect(parent.update_input)
        self.laps.valueChanged.connect(self.disable_race_minute)

        self.formation = QDoubleSpinBox()
        self.formation.setRange(0, 9999)
        self.formation.setDecimals(2)
        self.formation.setSingleStep(0.1)
        self.formation.setAlignment(Qt.AlignRight)
        self.formation.valueChanged.connect(parent.update_input)

        self.pit_seconds = QDoubleSpinBox()
        self.pit_seconds.setRange(0, 9999)
        self.pit_seconds.setDecimals(1)
        self.pit_seconds.setAlignment(Qt.AlignRight)
        self.pit_seconds.valueChanged.connect(parent.update_input)

        _add_output(0, 0, layout, self.minutes, "Race Minutes:", "min")
        _add_output(0, 2, layout, self.laps, "Race Laps:", "lap")
        _add_output(2, 0, layout, self.formation, "Formation/Rolling:", "lap")
        _add_output(2, 2, layout, self.pit_seconds, "Average Pit Seconds:", "sec")

    def disable_race_lap(self, value: int):
        """Disable race laps if race minutes is set"""
        if value > 0:
            if self.laps.isEnabled():
                self.laps.setValue(0)
                self.laps.setDisabled(True)
        else:
            self.laps.setDisabled(False)

    def disable_race_minute(self, value: int):
        """Disable race minutes if race laps is set"""
        if value > 0:
            if self.minutes.isEnabled():
                self.minutes.setValue(0)
                self.minutes.setDisabled(True)
        else:
            self.minutes.setDisabled(False)


class OutputUsage(QFrame):
    """Output usage display"""

    def __init__(self, parent, type_name: str) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        layout = _set_layout(QGridLayout(self))

        if type_name == "Fuel":
            unit_text = parent.symbol_fuel
        else:
            unit_text = "%"

        self.total_needed = QLineEdit("0.000 ≈ 0")
        self.total_needed.setAlignment(Qt.AlignRight)
        self.total_needed.setReadOnly(True)

        self.pit_stops = QLineEdit("0.000 ≈ 0")
        self.pit_stops.setAlignment(Qt.AlignRight)
        self.pit_stops.setReadOnly(True)

        self.total_laps = QLineEdit("0.000")
        self.total_laps.setAlignment(Qt.AlignRight)
        self.total_laps.setReadOnly(True)

        self.total_minutes = QLineEdit("0.000")
        self.total_minutes.setAlignment(Qt.AlignRight)
        self.total_minutes.setReadOnly(True)

        self.stint_laps = QLineEdit("0.000")
        self.stint_laps.setAlignment(Qt.AlignRight)
        self.stint_laps.setReadOnly(True)

        self.stint_minutes = QLineEdit("0.000")
        self.stint_minutes.setAlignment(Qt.AlignRight)
        self.stint_minutes.setReadOnly(True)

        self.final_laps = QLineEdit("0.000")
        self.final_laps.setAlignment(Qt.AlignRight)
        self.final_laps.setReadOnly(True)

        self.end_stint = QLineEdit("0.000")
        self.end_stint.setAlignment(Qt.AlignRight)
        self.end_stint.setReadOnly(True)

        self.one_less_stint = QLineEdit("0.000")
        self.one_less_stint.setAlignment(Qt.AlignRight)
        self.one_less_stint.setReadOnly(True)

        self.average_refill = QLineEdit("0.000")
        self.average_refill.setAlignment(Qt.AlignRight)
        self.average_refill.setReadOnly(True)

        _add_output(0, 0, layout, self.total_needed, f"Total Race {type_name}:", unit_text)
        _add_output(2, 0, layout, self.pit_stops, "Total Pit Stops:", "pit")
        _add_output(4, 0, layout, self.total_laps, "Total Race Laps:", "lap")
        _add_output(6, 0, layout, self.total_minutes, "Total Race Minutes:", "min")
        _add_output(8, 0, layout, self.stint_laps, "Max Stint Laps:", "lap")
        _add_output(10, 0, layout, self.stint_minutes, "Max Stint Minutes:", "min")
        _add_output(12, 0, layout, self.final_laps, "Final Stint Laps:", "lap")
        _add_output(14, 0, layout, self.end_stint, f"End Stint {type_name}:", unit_text)
        _add_output(16, 0, layout, self.one_less_stint, "One Less Pit Stop:", unit_text)
        _add_output(18, 0, layout, self.average_refill, "Average Refilling:", unit_text)


class InputWear(QFrame):
    """Input wear"""

    def __init__(self, parent, type_name: str) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        layout = _set_layout(QGridLayout(self))
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        if type_name == "Pad":
            self.effective = QDoubleSpinBox()
            self.effective.setRange(0, 99999)
            self.effective.setDecimals(6)
            self.effective.setSingleStep(1.0)
            self.effective.setAlignment(Qt.AlignRight)
            self.effective.valueChanged.connect(self.update_thickness)

            self.wear_millimeter = QDoubleSpinBox()
            self.wear_millimeter.setRange(0, 99999)
            self.wear_millimeter.setDecimals(6)
            self.wear_millimeter.setSingleStep(0.0001)
            self.wear_millimeter.setAlignment(Qt.AlignRight)
            self.wear_millimeter.valueChanged.connect(self.update_thickness)

        self.wear_start = QDoubleSpinBox()
        self.wear_start.setRange(0, 100)
        self.wear_start.setDecimals(3)
        self.wear_start.setSingleStep(0.01)
        self.wear_start.setAlignment(Qt.AlignRight)
        self.wear_start.setValue(100.0)
        self.wear_start.valueChanged.connect(parent.update_input)

        self.wear_lap = QDoubleSpinBox()
        self.wear_lap.setRange(0, 100)
        self.wear_lap.setDecimals(3)
        self.wear_lap.setSingleStep(0.01)
        self.wear_lap.setAlignment(Qt.AlignRight)
        self.wear_lap.valueChanged.connect(parent.update_input)

        self.wear_stint = QLineEdit("0.000")
        self.wear_stint.setAlignment(Qt.AlignRight)
        self.wear_stint.setReadOnly(True)

        self.lifespan_laps = QLineEdit("99999.000")
        self.lifespan_laps.setAlignment(Qt.AlignRight)
        self.lifespan_laps.setReadOnly(True)

        self.lifespan_minutes = QLineEdit("99999.000")
        self.lifespan_minutes.setAlignment(Qt.AlignRight)
        self.lifespan_minutes.setReadOnly(True)

        self.lifespan_stints = QLineEdit("0.000")
        self.lifespan_stints.setAlignment(Qt.AlignRight)
        self.lifespan_stints.setReadOnly(True)

        if type_name == "Pad":
            _add_output(0, 0, layout, self.effective, "Brake Pad Thickness:", "mm")
            _add_output(0, 2, layout, self.wear_millimeter, "Millimeter Wear Per Lap:", "mm")
        _add_output(2, 0, layout, self.wear_start, f"Starting {type_name} Life:", "%")
        _add_output(2, 2, layout, self.lifespan_laps, "Lifespan Laps:", "lap")
        _add_output(4, 0, layout, self.wear_lap, "Percent Wear Per Lap:", "%")
        _add_output(4, 2, layout, self.lifespan_minutes, "Lifespan Minutes:", "min")
        _add_output(6, 0, layout, self.wear_stint, "Percent Wear Per Stint:", "%")
        _add_output(6, 2, layout, self.lifespan_stints, "Lifespan Stints:", "x")

    def update_thickness(self, value: float):
        """Convert thickness to percent"""
        if value > 0:
            effective_thickness = self.effective.value()
            if effective_thickness > 0:
                wear_lap = self.wear_millimeter.value() * 100 / effective_thickness
            else:
                wear_lap = 0
            self.wear_lap.setValue(wear_lap)

    def update(self, stint_runlaps: float, laptime: float):
        """Calculate wear"""
        wear_start = self.wear_start.value()
        wear_lap = self.wear_lap.value()
        wear_stint = wear_lap * stint_runlaps

        lifespan_laps = calc.wear_lifespan_in_laps(wear_start, wear_lap, 99999)
        lifespan_mins = calc.wear_lifespan_in_mins(wear_start, wear_lap, laptime, 99999)
        lifespan_stints = lifespan_laps / stint_runlaps if stint_runlaps else 0

        self.lifespan_laps.setText(f"{lifespan_laps:.3f}")
        self.lifespan_minutes.setText(f"{lifespan_mins:.3f}")
        self.lifespan_stints.setText(f"{lifespan_stints:.3f}")

        self.wear_stint.setText(f"{wear_stint:.3f}")
        _highlight_invalid(self.lifespan_stints, 0 < lifespan_stints < 1)
        _highlight_invalid(self.wear_stint, wear_stint >= wear_start)
