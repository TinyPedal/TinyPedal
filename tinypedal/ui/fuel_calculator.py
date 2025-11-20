#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
from math import ceil, floor

from PySide2.QtCore import Qt
from PySide2.QtGui import QColor, QPainter
from PySide2.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import calculation as calc
from ..api_control import api
from ..const_file import FileFilter
from ..formatter import laptime_string_to_seconds
from ..module_info import ConsumptionDataSet, minfo
from ..setting import cfg
from ..units import set_symbol_fuel, set_unit_fuel
from ..userfile.consumption_history import load_consumption_history_file
from ._common import BaseDialog, UIScaler


def set_grid_layout(spacing: int = 2, margin: int = 4):
    """Set grid layout"""
    spacing = UIScaler.pixel(spacing)
    margin = UIScaler.pixel(margin)
    layout = QGridLayout()
    layout.setSpacing(spacing)
    layout.setContentsMargins(margin, margin, margin, margin)
    return layout


def highlight_invalid(line_edit: QLineEdit, invalid=False):
    """Highlight invalid"""
    line_edit.setStyleSheet("background: #F40;" if invalid else "")


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

        self.label_laps = QLabel("-")
        self.label_laps.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(frame, stretch=1)
        layout.addWidget(self.label_laps)
        self.setLayout(layout)

    def update_input(self, total_laps: float, stint_runlaps: float, start_runlaps: float):
        """Update input value"""
        self.floor_total_laps = floor(total_laps)
        self.floor_stint_runlaps = floor(stint_runlaps)
        self.floor_start_runlaps = floor(start_runlaps) if start_runlaps > 0 else self.floor_stint_runlaps
        self.label_laps.setText(str(self.floor_total_laps) if self.floor_total_laps else "-")
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


class FuelCalculator(BaseDialog):
    """Fuel calculator"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Fuel Calculator")

        # Set (freeze) fuel unit
        self.is_gallon = cfg.units["fuel_unit"] == "Gallon"
        self.unit_fuel = set_unit_fuel(cfg.units["fuel_unit"])
        self.symbol_fuel = set_symbol_fuel(cfg.units["fuel_unit"])

        # Set status bar
        self.status_bar = QStatusBar(self)

        # Set preview
        self.pit_preview = PitStopPreview(self)

        # Set view
        self.panel_calculator = QWidget(self)
        self.set_panel_calculator(self.panel_calculator)

        # Panel table
        self.panel_table = QWidget(self)
        self.set_panel_table(self.panel_table)

        # Load data
        self.load_live_data()

        # Layout
        layout_panel = QHBoxLayout()
        layout_panel.addWidget(self.panel_calculator)
        layout_panel.addWidget(self.panel_table)
        layout_main = QVBoxLayout()
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, 0)
        layout_main.addLayout(layout_panel, stretch=1)
        layout_main.addWidget(self.status_bar)
        self.setLayout(layout_main)
        self.setFixedWidth(self.sizeHint().width())

    def toggle_history_panel(self):
        """Toggle history data panel"""
        if self.panel_table.isHidden():
            self.panel_table.show()
            self.setFixedWidth(self.sizeHint().width())
            self.button_toggle.setText("Hide History")
        else:
            self.panel_table.hide()
            margin = self.layout().contentsMargins()
            self.setFixedWidth(self.panel_calculator.sizeHint().width() + margin.left() + margin.right())
            self.button_toggle.setText("Show History")

    def add_selected_data(self):
        """Add selected history data"""
        selected_data = self.table_history.selectedItems()
        if not selected_data:
            QMessageBox.warning(
                self, "Error",
                "No data selected.")
            return

        data_laptime = [data for data in selected_data if data.column() == 1]
        data_fuel = [data for data in selected_data if data.column() == 2]
        data_energy = [data for data in selected_data if data.column() == 3]
        data_tyrewear = [data for data in selected_data if data.column() == 6]
        data_capacity = [data for data in selected_data if data.column() == 7]

        # Send data to calculator
        if data_laptime:
            dataset = [laptime_string_to_seconds(data.text()) for data in data_laptime]
            output_value = calc.mean(dataset) if len(data_laptime) > 1 else dataset[0]
            self.input_laptime.minutes.setValue(output_value // 60)
            self.input_laptime.seconds.setValue(output_value % 60)
            self.input_laptime.mseconds.setValue(output_value % 1 * 1000)
        if data_fuel:
            dataset = [float(data.text()) for data in data_fuel]
            output_value = calc.mean(dataset) if len(data_fuel) > 1 else dataset[0]
            self.input_fuel.fuel_used.setValue(output_value)
        if data_energy:
            dataset = [float(data.text()) for data in data_energy]
            output_value = calc.mean(dataset) if len(data_energy) > 1 else dataset[0]
            self.input_fuel.energy_used.setValue(output_value)
        if data_tyrewear:
            dataset = [float(data.text()) for data in data_tyrewear]
            output_value = calc.mean(dataset) if len(data_tyrewear) > 1 else dataset[0]
            self.input_tyre.wear_lap.setValue(output_value)
        if data_capacity:
            output_value = float(data_capacity[0].text())
            self.input_fuel.capacity.setValue(output_value)

    def load_file(self):
        """Load history data from file"""
        filename_full = QFileDialog.getOpenFileName(
            self,
            dir=cfg.path.fuel_delta,
            filter=";;".join((FileFilter.CONSUMPTION, FileFilter.CSV))
        )[0]
        if not filename_full:
            return

        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.splitext(os.path.basename(filename_full))[0]
        history_data = load_consumption_history_file(
            filepath=filepath,
            filename=filename,
        )
        self.refresh_table(history_data)
        self.fill_in_data(history_data)
        self.status_bar.showMessage(f"File Source: {filename}")

    def load_live_data(self):
        """Load history data from live session"""
        self.refresh_table(minfo.history.consumptionDataSet)
        self.fill_in_data(minfo.history.consumptionDataSet)
        self.status_bar.showMessage(f"Live Source: {api.read.session.combo_name()}")

    def fill_in_data(self, dataset: deque[ConsumptionDataSet]):
        """Fill in history data to edit"""
        latest_history = dataset[0]
        # Load laptime from last valid lap
        laptime = latest_history.lapTimeLast
        if laptime > 0 and latest_history.isValidLap:
            self.input_laptime.minutes.setValue(laptime // 60)
            self.input_laptime.seconds.setValue(laptime % 60)
            self.input_laptime.mseconds.setValue(laptime % 1 * 1000)
        # Load tank capacity
        capacity = max(api.read.vehicle.tank_capacity(), latest_history.capacityFuel)
        if capacity:
            self.input_fuel.capacity.setValue(self.unit_fuel(capacity))
        # Load consumption from last valid lap
        if latest_history.isValidLap:
            fuel_used = latest_history.lastLapUsedFuel
            self.input_fuel.fuel_used.setValue(self.unit_fuel(fuel_used))
            energy_used = latest_history.lastLapUsedEnergy
            self.input_fuel.energy_used.setValue(energy_used)
            tyre_wear = latest_history.tyreAvgWearLast
            self.input_tyre.wear_lap.setValue(tyre_wear)

    def refresh_table(self, dataset: deque[ConsumptionDataSet]):
        """Refresh history data table"""
        self.table_history.setRowCount(0)
        invalid_color = QColor("#F40")
        flag_selectable = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        flag_unselectable = Qt.NoItemFlags

        for row_index, lap_data in enumerate(dataset):
            lapnumber = self.__add_table_item(f"{lap_data.lapNumber}", flag_unselectable)
            laptime = self.__add_table_item(calc.sec2laptime_full(lap_data.lapTimeLast), flag_selectable)
            used_fuel = self.__add_table_item(f"{self.unit_fuel(lap_data.lastLapUsedFuel):.3f}", flag_selectable)
            used_energy = self.__add_table_item(f"{lap_data.lastLapUsedEnergy:.3f}", flag_selectable)
            battery_drain = self.__add_table_item(f"{lap_data.batteryDrainLast:.3f}", flag_unselectable)
            battery_regen = self.__add_table_item(f"{lap_data.batteryRegenLast:.3f}", flag_unselectable)
            tyre_wear = self.__add_table_item(f"{lap_data.tyreAvgWearLast:.3f}", flag_selectable)
            capacity_fuel = self.__add_table_item(f"{self.unit_fuel(lap_data.capacityFuel):.3f}", flag_selectable)

            if not lap_data.isValidLap:  # set invalid lap text color
                laptime.setForeground(invalid_color)
                used_fuel.setForeground(invalid_color)
                used_energy.setForeground(invalid_color)

            self.table_history.insertRow(row_index)
            self.table_history.setItem(row_index, 0, lapnumber)
            self.table_history.setItem(row_index, 1, laptime)
            self.table_history.setItem(row_index, 2, used_fuel)
            self.table_history.setItem(row_index, 3, used_energy)
            self.table_history.setItem(row_index, 4, battery_drain)
            self.table_history.setItem(row_index, 5, battery_regen)
            self.table_history.setItem(row_index, 6, tyre_wear)
            self.table_history.setItem(row_index, 7, capacity_fuel)

    def __add_table_item(self, text: str, flags: Qt.ItemFlags):
        """Add table item"""
        item = QTableWidgetItem()
        item.setText(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(flags)
        return item

    def set_panel_calculator(self, panel):
        """Set panel calculator"""
        frame_laptime = QFrame(self)
        frame_laptime.setFrameShape(QFrame.StyledPanel)

        frame_fuel = QFrame(self)
        frame_fuel.setFrameShape(QFrame.StyledPanel)

        frame_race = QFrame(self)
        frame_race.setFrameShape(QFrame.StyledPanel)

        frame_output_fuel = QFrame(self)
        frame_output_fuel.setFrameShape(QFrame.StyledPanel)

        frame_output_energy = QFrame(self)
        frame_output_energy.setFrameShape(QFrame.StyledPanel)

        frame_output_start_fuel = QFrame(self)
        frame_output_start_fuel.setFrameShape(QFrame.StyledPanel)

        frame_output_start_energy = QFrame(self)
        frame_output_start_energy.setFrameShape(QFrame.StyledPanel)

        frame_output_tyre_wear = QFrame(self)
        frame_output_tyre_wear.setFrameShape(QFrame.StyledPanel)

        self.input_laptime = InputLapTime(self, frame_laptime)
        self.input_fuel = InputFuel(self, frame_fuel)
        self.input_race = InputRace(self, frame_race)

        self.usage_fuel = OutputUsage(self, frame_output_fuel, "Fuel")
        self.usage_energy = OutputUsage(self, frame_output_energy, "Energy")

        self.refill_fuel = InputRefill(self, frame_output_start_fuel, "Fuel")
        self.refill_energy = InputRefill(self, frame_output_start_energy, "Energy")

        self.input_tyre = InputTyreWear(self, frame_output_tyre_wear)

        button_loadlive = QPushButton("Load Live")
        button_loadlive.clicked.connect(self.load_live_data)
        button_loadlive.setFocusPolicy(Qt.NoFocus)

        button_loadfile = QPushButton("Load File")
        button_loadfile.clicked.connect(self.load_file)
        button_loadfile.setFocusPolicy(Qt.NoFocus)

        self.button_toggle = QPushButton("Hide History")
        self.button_toggle.clicked.connect(self.toggle_history_panel)
        self.button_toggle.setFocusPolicy(Qt.NoFocus)

        layout_usage = QHBoxLayout()
        layout_usage.addWidget(frame_output_fuel)
        layout_usage.addWidget(frame_output_energy)

        layout_refill = QHBoxLayout()
        layout_refill.addWidget(frame_output_start_fuel)
        layout_refill.addWidget(frame_output_start_energy)

        layout_calculator = QVBoxLayout()
        layout_calculator.setAlignment(Qt.AlignTop)
        layout_calculator.addWidget(frame_laptime)
        layout_calculator.addWidget(frame_fuel)
        layout_calculator.addWidget(frame_race)
        layout_calculator.addLayout(layout_usage)
        layout_calculator.addLayout(layout_refill)
        layout_calculator.addWidget(frame_output_tyre_wear)

        layout_data = QHBoxLayout()
        layout_data.addWidget(self.pit_preview)
        layout_data.addLayout(layout_calculator)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_loadlive, stretch=1)
        layout_button.addWidget(button_loadfile, stretch=1)
        layout_button.addStretch(1)
        layout_button.addWidget(self.button_toggle, stretch=2)

        layout_panel = QVBoxLayout()
        layout_panel.setContentsMargins(0, 0, 0, 0)
        layout_panel.addLayout(layout_data)
        layout_panel.addLayout(layout_button)
        panel.setLayout(layout_panel)

    def set_panel_table(self, panel):
        """Set panel table"""
        columns_stretch = 7
        self.table_history = QTableWidget(self)
        self.table_history.setColumnCount(1 + columns_stretch)
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_history.setColumnWidth(0, UIScaler.size(3))
        self.table_history.setFixedWidth(UIScaler.size(3 + 5 * columns_stretch))
        self.table_history.setHorizontalHeaderLabels((
            "Lap",
            "Time",
            f"Fuel({self.symbol_fuel})",
            "Energy(%)",
            "Drain(%)",
            "Regen(%)",
            "Tyre(%)",
            f"Tank({self.symbol_fuel})",
        ))

        button_adddata = QPushButton("Add Selected Data")
        button_adddata.clicked.connect(self.add_selected_data)
        button_adddata.setFocusPolicy(Qt.NoFocus)

        layout_panel = QVBoxLayout()
        layout_panel.setContentsMargins(0, 0, 0, 0)
        layout_panel.addWidget(self.table_history)
        layout_panel.addWidget(button_adddata)
        panel.setLayout(layout_panel)

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
        fuel_start = self.refill_fuel.amount_start.value(
            ) if self.refill_fuel.amount_start.value() else tank_capacity
        energy_used = self.input_fuel.energy_used.value()
        energy_start = self.refill_energy.amount_start.value(
            ) if self.refill_energy.amount_start.value() else 100

        # Calc fuel ratio
        if self.is_gallon:
            fuel_ratio = calc.fuel_to_energy_ratio(fuel_used * 3.785411784, energy_used)
        else:
            fuel_ratio = calc.fuel_to_energy_ratio(fuel_used, energy_used)
        self.input_fuel.fuel_ratio.setText(f"{fuel_ratio:.3f}")

        # Calc fuel
        fuel_total_runlaps, fuel_stint_runlaps, fuel_start_runlaps = self.calc_consumption(
            "fuel", tank_capacity, fuel_used, fuel_start, total_race_seconds,
            absolute_race_laps, total_formation_laps, average_pit_seconds, laptime)

        # Calc energy
        energy_total_runlaps, energy_stint_runlaps, energy_start_runlaps = self.calc_consumption(
            "energy", 100, energy_used, energy_start, total_race_seconds,
            absolute_race_laps, total_formation_laps, average_pit_seconds, laptime)

        # Calc tyre
        self.calc_tyre_consumption(fuel_stint_runlaps, energy_stint_runlaps, laptime)

        # Update pit preview
        if energy_used > 0:
            self.pit_preview.update_input(energy_total_runlaps, energy_stint_runlaps, energy_start_runlaps)
        else:
            self.pit_preview.update_input(fuel_total_runlaps, fuel_stint_runlaps, fuel_start_runlaps)

    def calc_consumption(self, output_type, tank_capacity, consumption, fuel_start,
        total_race_seconds, absolute_race_laps, total_formation_laps, average_pit_seconds, laptime):
        """Calculate and output results"""
        estimate_pit_counts = 0
        minimum_pit_counts = 0  # minimum pit stop required to finish race
        loop_counts = 10  # max loop limit

        start_runlaps = calc.end_stint_laps(fuel_start, consumption)

        # Total pit seconds depends on estimated pit counts
        # Recalculate and find nearest minimum pit counts on previous loop
        while loop_counts:
            minimum_pit_counts = ceil(estimate_pit_counts)
            if total_race_seconds:  # time-type race
                total_pit_seconds = minimum_pit_counts * average_pit_seconds
                total_race_laps = total_formation_laps + calc.time_type_full_laps_remain(
                    laptime, total_race_seconds - total_pit_seconds)
            else:  # lap-type race
                total_race_laps = total_formation_laps + absolute_race_laps

            total_need_frac = calc.total_fuel_needed(total_race_laps, consumption, 0)

            # Keep 1 decimal place for Gallon
            if self.is_gallon and output_type == "fuel":
                total_need_full = ceil(total_need_frac * 10) / 10
            else:
                total_need_full = ceil(total_need_frac)

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
                minimum_pit_counts == floor(estimate_pit_counts)):
                loop_counts = 1

            if minimum_pit_counts == ceil(estimate_pit_counts):
                break

        total_runlaps = calc.end_stint_laps(total_need_full, consumption)

        total_runmins = calc.end_stint_minutes(total_runlaps, laptime)

        used_one_less = calc.one_less_pit_stop_consumption(
            estimate_pit_counts, tank_capacity, amount_curr, total_race_laps)

        if minimum_pit_counts:
            average_refuel = (
                total_need_full - fuel_start + minimum_pit_counts * end_stint_fuel
                ) / minimum_pit_counts
        elif fuel_start < total_need_full <= tank_capacity:
            average_refuel = total_need_full - fuel_start
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
            output_refill = self.refill_fuel
        else:
            output_usage = self.usage_energy
            output_refill = self.refill_energy

        output_usage.total_needed.setText(
            f"{total_need_frac:.3f} ≈ {total_need_full}")
        output_usage.end_stint.setText(
            f"{end_stint_fuel:.3f}")
        output_usage.pit_stops.setText(
            f"{max(estimate_pit_counts, 0):.3f} ≈ {max(ceil(minimum_pit_counts), 0)}")
        output_usage.one_less_stint.setText(
            f"{max(used_one_less, 0):.3f}")
        output_usage.total_laps.setText(
            f"{total_runlaps:.3f}")
        output_usage.total_minutes.setText(
            f"{total_runmins:.3f}")
        output_usage.stint_laps.setText(
            f"{stint_runlaps:.3f}")
        output_usage.stint_minutes.setText(
            f"{stint_runmins:.3f}")

        output_refill.average_refill.setText(
            f"{average_refuel:.3f}")
        # Set warning color if exceeded tank capacity
        highlight_invalid(output_refill.average_refill, average_refuel > tank_capacity)
        return total_runlaps, stint_runlaps, start_runlaps

    def calc_tyre_consumption(self, fuel_stint_runlaps, energy_stint_runlaps, laptime):
        """Calculate tyre consumption"""
        # Pick the least runnable laps if both energy & fuel available
        if energy_stint_runlaps > 0 < fuel_stint_runlaps:
            stint_runlaps = min(fuel_stint_runlaps, energy_stint_runlaps)
        else:
            stint_runlaps = fuel_stint_runlaps

        tyre_start_tread = self.input_tyre.start_tread.value()
        tyre_wear_lap = self.input_tyre.wear_lap.value()
        tyre_wear_stint = tyre_wear_lap * stint_runlaps

        tyre_lifespan_laps = calc.wear_lifespan_in_laps(tyre_start_tread, tyre_wear_lap)
        tyre_lifespan_mins = calc.wear_lifespan_in_mins(tyre_start_tread, tyre_wear_lap, laptime)
        tyre_lifespan_stints = tyre_lifespan_laps / stint_runlaps if stint_runlaps else 0

        self.input_tyre.lifespan_laps.setText(f"{tyre_lifespan_laps:.3f}")
        self.input_tyre.lifespan_minutes.setText(f"{tyre_lifespan_mins:.3f}")
        self.input_tyre.lifespan_stints.setText(f"{tyre_lifespan_stints:.3f}")

        self.input_tyre.wear_stint.setText(f"{tyre_wear_stint:.3f}")
        highlight_invalid(self.input_tyre.lifespan_stints, 0 < tyre_lifespan_stints < 1)
        highlight_invalid(self.input_tyre.wear_stint, tyre_wear_stint >= tyre_start_tread)

    def validate_starting_fuel(self):
        """Validate starting fuel"""
        if self.refill_fuel.amount_start.value() > self.input_fuel.capacity.value():
            self.refill_fuel.amount_start.setValue(self.input_fuel.capacity.value())


class InputLapTime():
    """Input lap time setup"""

    def __init__(self, parent, frame) -> None:
        """Set input lap time"""
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

        layout = set_grid_layout()

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(4, 1)

        layout.addWidget(QLabel("Lap Time:"), 0, 0, 1, 6)

        layout.addWidget(self.minutes, 1, 0)
        layout.addWidget(QLabel("m"), 1, 1)

        layout.addWidget(self.seconds, 1, 2)
        layout.addWidget(QLabel("s"), 1, 3)

        layout.addWidget(self.mseconds, 1, 4)
        layout.addWidget(QLabel("ms"), 1, 5)

        frame.setLayout(layout)

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


class InputFuel():
    """Input fuel setup"""

    def __init__(self, parent, frame) -> None:
        """Set input fuel"""
        self.capacity = QDoubleSpinBox()
        self.capacity.setRange(0, 9999)
        self.capacity.setDecimals(2)
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

        layout = set_grid_layout()

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        layout.addWidget(QLabel("Tank Capacity:"), 0, 0, 1, 2)
        layout.addWidget(self.capacity, 1, 0)
        layout.addWidget(QLabel(parent.symbol_fuel), 1, 1)

        layout.addWidget(QLabel("Fuel Ratio:"), 2, 0, 1, 2)
        layout.addWidget(self.fuel_ratio, 3, 0)

        layout.addWidget(QLabel("Fuel Consumption:"), 0, 2, 1, 2)
        layout.addWidget(self.fuel_used, 1, 2)
        layout.addWidget(QLabel(parent.symbol_fuel), 1, 3)

        layout.addWidget(QLabel("Energy Consumption:"), 2, 2, 1, 2)
        layout.addWidget(self.energy_used, 3, 2)
        layout.addWidget(QLabel("%"), 3, 3)

        frame.setLayout(layout)


class InputRace():
    """Input race setup"""

    def __init__(self, parent, frame) -> None:
        """Set input race"""
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

        layout = set_grid_layout()

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        layout.addWidget(QLabel("Race Minutes:"), 0, 0, 1, 2)
        layout.addWidget(self.minutes, 1, 0)
        layout.addWidget(QLabel("min"), 1, 1)

        layout.addWidget(QLabel("Race Laps:"), 0, 2, 1, 2)
        layout.addWidget(self.laps, 1, 2)
        layout.addWidget(QLabel("lap"), 1, 3)

        layout.addWidget(QLabel("Formation/Rolling:"), 2, 0, 1, 2)
        layout.addWidget(self.formation, 3, 0)
        layout.addWidget(QLabel("lap"), 3, 1)

        layout.addWidget(QLabel("Average Pit Seconds:"), 2, 2, 1, 2)
        layout.addWidget(self.pit_seconds, 3, 2)
        layout.addWidget(QLabel("sec"), 3, 3)

        frame.setLayout(layout)

    def disable_race_lap(self):
        """Disable race laps if race minutes is set"""
        if self.minutes.value() > 0:
            if self.laps.isEnabled():
                self.laps.setValue(0)
                self.laps.setDisabled(True)
        else:
            self.laps.setDisabled(False)

    def disable_race_minute(self):
        """Disable race minutes if race laps is set"""
        if self.laps.value() > 0:
            if self.minutes.isEnabled():
                self.minutes.setValue(0)
                self.minutes.setDisabled(True)
        else:
            self.minutes.setDisabled(False)


class OutputUsage():
    """Output usage display"""

    def __init__(self, parent, frame, type_name) -> None:
        """Set output display"""
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

        self.end_stint = QLineEdit("0.000")
        self.end_stint.setAlignment(Qt.AlignRight)
        self.end_stint.setReadOnly(True)

        self.one_less_stint = QLineEdit("0.000")
        self.one_less_stint.setAlignment(Qt.AlignRight)
        self.one_less_stint.setReadOnly(True)

        layout = set_grid_layout()

        layout.addWidget(QLabel(f"Total Race {type_name}:"), 0, 0, 1, 2)
        layout.addWidget(self.total_needed, 1, 0)
        layout.addWidget(QLabel(unit_text), 1, 1)

        layout.addWidget(QLabel("Total Pit Stops:"), 2, 0, 1, 2)
        layout.addWidget(self.pit_stops, 3, 0)
        layout.addWidget(QLabel("pit"), 3, 1)

        layout.addWidget(QLabel("Total Laps:"), 4, 0, 1, 2)
        layout.addWidget(self.total_laps, 5, 0)
        layout.addWidget(QLabel("lap"), 5, 1)

        layout.addWidget(QLabel("Total Minutes:"), 6, 0, 1, 2)
        layout.addWidget(self.total_minutes, 7, 0)
        layout.addWidget(QLabel("min"), 7, 1)

        layout.addWidget(QLabel("Max Stint Laps:"), 8, 0, 1, 2)
        layout.addWidget(self.stint_laps, 9, 0)
        layout.addWidget(QLabel("lap"), 9, 1)

        layout.addWidget(QLabel("Max Stint Minutes:"), 10, 0, 1, 2)
        layout.addWidget(self.stint_minutes, 11, 0)
        layout.addWidget(QLabel("min"), 11, 1)

        layout.addWidget(QLabel(f"End Stint {type_name}:"), 12, 0, 1, 2)
        layout.addWidget(self.end_stint, 13, 0)
        layout.addWidget(QLabel(unit_text), 13, 1)

        layout.addWidget(QLabel("One Less Pit Stop:"), 14, 0, 1, 2)
        layout.addWidget(self.one_less_stint, 15, 0)
        layout.addWidget(QLabel(unit_text), 15, 1)

        frame.setLayout(layout)


class InputRefill():
    """Input refill display"""

    def __init__(self, parent, frame, type_name) -> None:
        """Set output display"""
        self.amount_start = QDoubleSpinBox()
        self.amount_start.setDecimals(2)
        self.amount_start.setAlignment(Qt.AlignRight)

        if type_name == "Fuel":
            start_range = 9999
            unit_text = parent.symbol_fuel
            self.amount_start.valueChanged.connect(parent.validate_starting_fuel)
        else:
            start_range = 100
            unit_text = "%"
        self.amount_start.setRange(0, start_range)
        self.amount_start.valueChanged.connect(parent.update_input)

        self.average_refill = QLineEdit("0.000")
        self.average_refill.setAlignment(Qt.AlignRight)
        self.average_refill.setReadOnly(True)

        layout = set_grid_layout()

        layout.addWidget(QLabel(f"Starting {type_name}:"), 0, 0, 1, 2)
        layout.addWidget(self.amount_start, 1, 0)
        layout.addWidget(QLabel(unit_text), 1, 1)

        layout.addWidget(QLabel("Average Refilling:"), 2, 0, 1, 2)
        layout.addWidget(self.average_refill, 3, 0)
        layout.addWidget(QLabel(unit_text), 3, 1)

        frame.setLayout(layout)


class InputTyreWear():
    """Input tyre wear"""

    def __init__(self, parent, frame) -> None:
        """Set input race"""
        self.start_tread = QDoubleSpinBox()
        self.start_tread.setRange(0, 100)
        self.start_tread.setDecimals(3)
        self.start_tread.setSingleStep(0.01)
        self.start_tread.setAlignment(Qt.AlignRight)
        self.start_tread.setValue(100.0)
        self.start_tread.valueChanged.connect(parent.update_input)

        self.wear_lap = QDoubleSpinBox()
        self.wear_lap.setRange(0, 100)
        self.wear_lap.setDecimals(3)
        self.wear_lap.setSingleStep(0.01)
        self.wear_lap.setAlignment(Qt.AlignRight)
        self.wear_lap.valueChanged.connect(parent.update_input)

        self.wear_stint = QLineEdit("0.000")
        self.wear_stint.setAlignment(Qt.AlignRight)
        self.wear_stint.setReadOnly(True)

        self.lifespan_laps = QLineEdit("0.000")
        self.lifespan_laps.setAlignment(Qt.AlignRight)
        self.lifespan_laps.setReadOnly(True)

        self.lifespan_minutes = QLineEdit("0.000")
        self.lifespan_minutes.setAlignment(Qt.AlignRight)
        self.lifespan_minutes.setReadOnly(True)

        self.lifespan_stints = QLineEdit("0.000")
        self.lifespan_stints.setAlignment(Qt.AlignRight)
        self.lifespan_stints.setReadOnly(True)

        layout = set_grid_layout()

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        layout.addWidget(QLabel("Starting Tyre Tread:"), 0, 0, 1, 2)
        layout.addWidget(self.start_tread, 1, 0)
        layout.addWidget(QLabel("%"), 1, 1)

        layout.addWidget(QLabel("Lifespan Laps:"), 0, 2, 1, 2)
        layout.addWidget(self.lifespan_laps, 1, 2)
        layout.addWidget(QLabel("lap"), 1, 3)

        layout.addWidget(QLabel("Tread Wear Per Lap:"), 2, 0, 1, 2)
        layout.addWidget(self.wear_lap, 3, 0)
        layout.addWidget(QLabel("%"), 3, 1)

        layout.addWidget(QLabel("Lifespan Minutes:"), 2, 2, 1, 2)
        layout.addWidget(self.lifespan_minutes, 3, 2)
        layout.addWidget(QLabel("min"), 3, 3)

        layout.addWidget(QLabel("Tread Wear Per Stint:"), 4, 0, 1, 2)
        layout.addWidget(self.wear_stint, 5, 0)
        layout.addWidget(QLabel("%"), 5, 1)

        layout.addWidget(QLabel("Lifespan Stints:"), 4, 2, 1, 2)
        layout.addWidget(self.lifespan_stints, 5, 2)
        layout.addWidget(QLabel("x"), 5, 3)

        frame.setLayout(layout)
