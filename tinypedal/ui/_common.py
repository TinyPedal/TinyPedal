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
Common
"""

import os
import re
from collections import deque
from typing import Callable

from PySide2.QtCore import QRegularExpression, Qt
from PySide2.QtGui import (
    QColor,
    QDoubleValidator,
    QIntValidator,
    QRegularExpressionValidator,
    qGray,
)
from PySide2.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..const_app import APP_NAME
from ..const_file import FileFilter
from ..module_control import mctrl, wctrl
from ..userfile import set_relative_path
from ..validator import image_exists, is_hex_color, is_string_number

# Validator
QVAL_INTEGER = QIntValidator(-999999, 999999)
QVAL_FLOAT = QDoubleValidator(-999999.9999, 999999.9999, 6)
QVAL_COLOR = QRegularExpressionValidator(QRegularExpression('^#[0-9a-fA-F]*'))
QVAL_HEATMAP = QRegularExpressionValidator(QRegularExpression('[0-9a-zA-Z_]*'))
QVAL_FILENAME = QRegularExpressionValidator(QRegularExpression('[^\\\\/:*?"<>|]*'))

# Misc
color_pick_history = deque(
    ["#FFF"] * QColorDialog.customCount(),
    maxlen=QColorDialog.customCount()
)


class UIScaler:
    """UI font & size scaler"""
    # Global base font size in point (not counting dpi scale)
    FONT_BASE_POINT = QApplication.font().pointSize()
    # Global base font size in pixel (dpi scaled)
    # dpi scale = font dpi / 96
    # px = (pt * dpi scale) * 96 / 72
    # px = pt * font dpi / 72
    FONT_DPI_SCALE = QApplication.fontMetrics().fontDpi() / 96
    FONT_BASE_PIXEL_SCALED = QApplication.font().pointSize() * QApplication.fontMetrics().fontDpi() / 72

    @staticmethod
    def font(scale: float) -> float:
        """Scale UI font size (points) by base font size (not counting dpi scale)"""
        return UIScaler.FONT_BASE_POINT * scale

    @staticmethod
    def size(scale: float) -> int:
        """Scale UI size (pixels) by base font size (scaled with dpi)"""
        return round(UIScaler.FONT_BASE_PIXEL_SCALED * scale)

    @staticmethod
    def pixel(pixel: int):
        """Scale pixel size by base font DPI scale"""
        return round(UIScaler.FONT_DPI_SCALE * pixel)


class CompactButton(QPushButton):
    """Compact button style"""

    def __init__(self, text, parent=None, has_menu=False):
        super().__init__(text, parent)
        self.setFixedWidth(
            self.fontMetrics().boundingRect(text).width()
            + UIScaler.FONT_BASE_PIXEL_SCALED * (1 + has_menu)
        )


# Class
class BaseDialog(QDialog):
    """Base dialog class"""
    MARGIN = UIScaler.pixel(6)

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

    def set_config_title(self, option_name: str, preset_name: str):
        """Set config dialog title"""
        self.setWindowTitle(f"{option_name} - {preset_name}")

    def set_utility_title(self, name: str):
        """Set utility dialog title"""
        self.setWindowTitle(f"{name} - {APP_NAME}")

    def confirm_operation(self, title: str = "Confirm", message: str = "") -> bool:
        """Confirm operation"""
        confirm = QMessageBox.question(
            self, title, message,
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        return confirm == QMessageBox.Yes


class BaseEditor(BaseDialog):
    """Base editor class"""

    def __init__(self, parent):
        super().__init__(parent)
        self._is_modified = False
        self._is_rejected = False

    def confirm_discard(self) -> bool:
        """Confirm save or discard changes"""
        if not self._is_modified:
            return True

        confirm = QMessageBox.question(
            self, "Confirm", "<b>Save changes before continue?</b>",
            buttons=QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

        if confirm == QMessageBox.Save:
            self.saving()
            return self.confirm_discard()

        return confirm == QMessageBox.Discard

    def is_modified(self) -> bool:
        """Is modified"""
        return self._is_modified

    def set_modified(self):
        """Set modified state"""
        if not self._is_modified:
            self._is_modified = True

    def set_unmodified(self):
        """Set unmodified state"""
        if self._is_modified:
            self._is_modified = False

    def saving(self):
        """Save changes"""

    def reject(self):
        """Reject(ESC) confirm"""
        if self.confirm_discard():
            self._is_rejected = True
            self.close()

    def closeEvent(self, event):
        """Close editor"""
        if self._is_rejected:
            return
        if not self.confirm_discard():
            event.ignore()

    @staticmethod
    def new_name_increment(name: str, table: QTableWidget, column: int = 0) -> str:
        """New name with number increment add at the end"""
        new_index = 1
        new_name = f"{name} {new_index}"
        exist = True
        while exist:  # check existing name
            items = table.findItems(new_name, Qt.MatchExactly)
            for item in items:
                if item.column() == column:  # match column
                    new_index += 1
                    new_name = f"{name} {new_index}"
                    break
            else:
                exist = False
        return new_name

    @staticmethod
    def is_value_in_table(target: str, table: QTableWidget, column: int = 0) -> bool:
        """Is there any matching value in table"""
        items = table.findItems(target, Qt.MatchExactly)
        for item in items:
            if item.column() == column:
                return True
        return False

    @staticmethod
    def reloading(reload_module: bool = True, reload_widget: bool = True) -> None:
        """Reloading"""
        if reload_module:
            mctrl.reload()
        if reload_widget:
            wctrl.reload()


class BatchOffset(BaseDialog):
    """Batch offset"""

    def __init__(self, parent, offset_func: Callable):
        super().__init__(parent)
        self.setWindowTitle("Batch Offset")
        self.decimals = 0
        self.value_range = 0, 1
        self.offset_func = offset_func
        self.edit_offset = QDoubleSpinBox()
        self.last_offset = QLabel("0")
        self.last_label = QLabel("Last Offset:")
        self.checkbox_scale = QCheckBox("Scale Mode")

    def config(self, decimals: int, step: float, min_range: int, max_range: int):
        """Config offset"""
        self.decimals = decimals
        self.value_range = min_range, max_range

        # Label
        layout_label = QHBoxLayout()
        layout_label.addWidget(self.last_label)
        layout_label.addStretch(1)
        layout_label.addWidget(self.last_offset)

        # Edit offset
        self.edit_offset.setDecimals(self.decimals)
        self.edit_offset.setRange(*self.value_range)
        self.edit_offset.setSingleStep(step)
        self.edit_offset.setAlignment(Qt.AlignRight)

        # Scale mode
        self.checkbox_scale.setChecked(False)
        self.checkbox_scale.toggled.connect(self.toggle_mode)

        # Button
        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)

        button_close = QDialogButtonBox(QDialogButtonBox.Close)
        button_close.rejected.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_apply)
        layout_button.addStretch(1)
        layout_button.addWidget(button_close)

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_label)
        layout_main.addWidget(self.edit_offset)
        layout_main.addWidget(self.checkbox_scale)
        layout_main.addLayout(layout_button)
        self.setLayout(layout_main)
        self.setFixedSize(UIScaler.size(12), self.sizeHint().height())

    def toggle_mode(self, checked: bool):
        """Toggle mode"""
        self.last_offset.setText("0")
        if checked:
            self.edit_offset.setRange(0, 100)
            self.edit_offset.setDecimals(6)
            self.last_label.setText("Last Scale:")
        else:
            self.edit_offset.setRange(*self.value_range)
            self.edit_offset.setDecimals(self.decimals)
            self.last_label.setText("Last Offset:")

    def applying(self):
        """Apply offset"""
        value = self.edit_offset.value()
        if value != 0:
            self.offset_func(value, self.checkbox_scale.isChecked())
            offset_text = f"{value:.{self.edit_offset.decimals()}f}"
            self.last_offset.setText(offset_text.rstrip("0").rstrip("."))
            self.edit_offset.setValue(0)


class TableBatchReplace(BaseDialog):
    """Table batch replace"""

    def __init__(
        self, parent, table_selector: dict, table_data: QTableWidget):
        """
        Args:
            table_selector: table selector dictionary. key=column name, value=column index.
        """
        super().__init__(parent)
        self.table_selector = table_selector
        self.table_data = table_data
        self.setWindowTitle("Batch Replace")

        # Label & combobox
        self.search_selector = QComboBox()
        self.search_selector.setEditable(True)
        self.search_selector.setCompleter(QCompleter())  # disable auto-complete

        self.column_selector = QComboBox()
        self.column_selector.addItems(list(self.table_selector))
        self.column_selector.currentIndexChanged.connect(self.update_selector)
        self.update_selector(self.table_selector[self.column_selector.currentText()])

        self.replace_entry = QLineEdit()

        self.checkbox_casematch = QCheckBox("Match Case")
        self.checkbox_casematch.setChecked(False)
        self.checkbox_exactmatch = QCheckBox("Match Whole Word")
        self.checkbox_exactmatch.setChecked(False)

        layout_option = QGridLayout()
        layout_option.setAlignment(Qt.AlignTop)
        layout_option.addWidget(QLabel("Column:"), 0, 0)
        layout_option.addWidget(QLabel("Find:"), 1, 0)
        layout_option.addWidget(QLabel("Replace:"), 2, 0)
        layout_option.addWidget(self.column_selector, 0, 1)
        layout_option.addWidget(self.search_selector, 1, 1)
        layout_option.addWidget(self.replace_entry, 2, 1)
        layout_option.addWidget(self.checkbox_exactmatch, 3, 1)
        layout_option.addWidget(self.checkbox_casematch, 4, 1)

        # Button
        button_replace = QPushButton("Replace")
        button_replace.clicked.connect(self.replacing)

        button_close = QDialogButtonBox(QDialogButtonBox.Close)
        button_close.rejected.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_replace)
        layout_button.addStretch(1)
        layout_button.addWidget(button_close)

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_option)
        layout_main.addLayout(layout_button)
        self.setLayout(layout_main)
        self.setMinimumWidth(UIScaler.size(22))
        self.setFixedHeight(self.sizeHint().height())

    def update_selector(self, column_index: int, last_search: str = ""):
        """Update selector list"""
        column_index = self.table_selector[self.column_selector.currentText()]
        self.search_selector.clear()
        selector_list = set(
            self.table_data.item(row_index, column_index).text()
            for row_index in range(self.table_data.rowCount())
        )
        self.search_selector.addItems(sorted(selector_list))
        self.search_selector.setCurrentText(last_search)

    def replacing(self):
        """Replace"""
        if not self.search_selector.currentText():
            QMessageBox.warning(self, "Error", "Invalid name.")
            return

        column_index = self.table_selector[self.column_selector.currentText()]
        search = self.search_selector.currentText()
        replace = self.replace_entry.text()

        pattern = re.escape(search)  # escape special chars
        if self.checkbox_exactmatch.isChecked():
            pattern = f"^{pattern}$"

        if self.checkbox_casematch.isChecked():
            match_flag = 0
        else:
            match_flag = re.IGNORECASE

        for row_index in range(self.table_data.rowCount()):
            item = self.table_data.item(row_index, column_index)
            item.setText(re.sub(pattern, replace, item.text(), flags=match_flag))

        self.update_selector(column_index, search)


class DoubleClickEdit(QLineEdit):
    """Line edit with double click dialog trigger"""

    def __init__(self, parent, mode: str, init: str):
        """Set dialog mode and initial value

        Args:
            mode: "color", "path".
            init: initial value.
        """
        super().__init__(parent)
        self.open_mode = mode
        self.init_value = init

    def mouseDoubleClickEvent(self, event):
        """Double click to open dialog"""
        if event.buttons() == Qt.LeftButton:
            if self.open_mode == "color":
                self.open_dialog_color()
            elif self.open_mode == "path":
                self.open_dialog_path()
            elif self.open_mode == "image":
                self.open_dialog_image()

    def open_dialog_color(self):
        """Open color dialog"""
        color_dialog = QColorDialog()
        # Load color history to custom color slot
        for index, old_color in enumerate(color_pick_history):
            color_dialog.setCustomColor(index, QColor(old_color))
        # Open color selector dialog
        color_get = color_dialog.getColor(
            initial=QColor(self.init_value),
            options=QColorDialog.ShowAlphaChannel
        )
        if color_get.isValid():
            # Add new color to color history
            if color_pick_history[0] != color_get:
                color_pick_history.appendleft(color_get)
            # Set output format
            if color_get.alpha() == 255:  # without alpha value
                color = color_get.name(QColor.HexRgb).upper()
            else:  # with alpha value
                color = color_get.name(QColor.HexArgb).upper()
            # Update edit box and init value
            self.setText(color)
            self.init_value = color

    def open_dialog_path(self):
        """Open file path dialog"""
        path_selected = QFileDialog.getExistingDirectory(self, dir=self.init_value)
        if os.path.exists(path_selected):
            # Convert to relative path if in APP root folder
            path_valid = set_relative_path(path_selected)
            # Update edit box and init value
            self.setText(path_valid)
            self.init_value = path_valid

    def open_dialog_image(self):
        """Open image file name dialog"""
        path_selected = QFileDialog.getOpenFileName(self, dir=self.init_value, filter=FileFilter.PNG)[0]
        if image_exists(path_selected):
            self.setText(path_selected)
            self.init_value = path_selected

    def preview_color(self):
        """Update edit preview color"""
        color_str = self.text()
        if is_hex_color(color_str):
            # Set foreground color based on background color lightness
            qcolor = QColor(color_str)
            if qcolor.alpha() > 128 > qGray(qcolor.rgb()):
                fg_color = "#FFF"
            else:
                fg_color = "#000"
            # Apply style
            self.setStyleSheet(f"QLineEdit {{color:{fg_color};background:{color_str};}}")


class FloatTableItem(QTableWidgetItem):
    """QTable item - float type with validation"""

    def __init__(self, value: float):
        """Convert & set float value to string"""
        super().__init__()
        self._value = 0.0
        self.setValue(value)

    def setValue(self, value: float):
        """Set value"""
        self._value = value
        self.setText(str(value))

    def value(self) -> float:
        """Get value"""
        return self._value

    def validate(self):
        """Validate value, replace invalid value with old value if invalid"""
        value = self.text()
        if is_string_number(value):
            self._value = float(value)
        else:
            self.setText(str(self._value))

    def __lt__(self, other):
        """Sort by value"""
        return self.value() < other.value()


class NumericTableItem(QTableWidgetItem):
    """QTable item - sortable numeric text"""

    def __init__(self, value: float, text: str):
        """Set numeric value & string text"""
        super().__init__()
        self.value = value
        self.setText(text)

    def __lt__(self, other):
        """Sort by value"""
        return self.value < other.value
