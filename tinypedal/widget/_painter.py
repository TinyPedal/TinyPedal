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
Overlay base painter class.
"""

from __future__ import annotations

from typing import Any

from PySide2.QtCore import QRectF, Qt
from PySide2.QtGui import QFont, QPainter, QPen, QPixmap
from PySide2.QtWidgets import QWidget


class WheelGaugeBar(QWidget):
    """Wheel gauge bar"""

    def __init__(
        self,
        parent,
        padding_x: int,
        bar_width: int,
        bar_height: int,
        offset_y: int = 0,
        decimals: int = 0,
        display_range: int = 100,
        input_color: str = "",
        fg_color: str = "",
        bg_color: str = "",
        mark_width: int = 0,
        mark_color: str = "",
        maxrange_height: int = 0,
        maxrange_color: str = "",
        maxreading_width: int = 0,
        maxreading_color: str = "",
        right_side: bool = False,
        top_side: bool = True,
    ):
        super().__init__(parent)
        self.last = -1
        self.max_value = 0
        self.input_color = input_color
        self.bg_color = bg_color
        self.mark_color = mark_color
        self.maxrange_color = maxrange_color
        self._display_range = display_range
        self._decimals = max(decimals, 0)
        self._width_scale = bar_width / self._display_range
        self._rect_bg = QRectF(0, 0, bar_width, bar_height)
        self._rect_input = self._rect_bg.adjusted(0, 0, 0, 0)
        self._rect_text = self._rect_bg.adjusted(padding_x, offset_y, -padding_x, 0)
        self._right_side = right_side
        self._pen = QPen()
        self._pen.setColor(fg_color)

        if maxreading_width > 0:
            self._pen_max = QPen()
            self._pen_max.setColor(maxreading_color)
            self._rect_max_text = self._rect_text.adjusted(0, 0, 0, 0)
            if right_side:
                self._rect_text.adjust(0, 0, -maxreading_width, 0)
            else:
                self._rect_text.adjust(maxreading_width, 0, 0, 0)
        else:
            self._rect_max_text = None

        if mark_color:
            self._rect_mark = QRectF(0, 0, mark_width, bar_height)
        else:
            self._rect_mark = self._rect_bg

        if maxrange_color:
            if top_side:
                self._rect_max = QRectF(0, 0, bar_width, maxrange_height)
            else:
                self._rect_max = QRectF(0, bar_height - maxrange_height, bar_width, maxrange_height)
            if right_side:
                self._rect_max.setWidth(0)
            else:
                self._rect_max.setX(bar_width)
        else:
            self._rect_max = self._rect_bg

        if right_side:
            self._alignment = Qt.AlignRight | Qt.AlignVCenter
        else:
            self._alignment = Qt.AlignLeft | Qt.AlignVCenter

        self.setFixedSize(bar_width, bar_height)

    def update_input(self, input_value: float):
        """Update input value"""
        if self._right_side:
            self._rect_input.setWidth(input_value * self._width_scale)
        else:
            self._rect_input.setX((self._display_range - input_value) * self._width_scale)
        self.update()

    def update_mark(self, mark_value: float):
        """Update mark"""
        if self._right_side:
            self._rect_mark.moveRight(mark_value * self._width_scale)
        else:
            self._rect_mark.moveLeft((self._display_range - mark_value) * self._width_scale)

    def update_maxrange(self, input_value: float):
        """Update max range"""
        if self._right_side:
            self._rect_max.setWidth(input_value * self._width_scale)
        else:
            self._rect_max.setX((self._display_range - input_value) * self._width_scale)
        self.max_value = input_value

    def paintEvent(self, event):
        """Draw normal without warning or negative highlighting"""
        painter = QPainter(self)
        painter.fillRect(self._rect_bg, self.bg_color)
        painter.fillRect(self._rect_input, self.input_color)
        if self.mark_color:
            painter.fillRect(self._rect_mark, self.mark_color)
        if self.maxrange_color:
            painter.fillRect(self._rect_max, self.maxrange_color)
        painter.setPen(self._pen)
        painter.drawText(self._rect_text, self._alignment, f"{self.last:.{self._decimals}f}")
        if self._rect_max_text:
            painter.setPen(self._pen_max)
            painter.drawText(self._rect_max_text, self._alignment, f"{self.max_value:.{self._decimals}f}")


class _PedalInputBar(QWidget):
    """Pedal input bar"""

    def __init__(
        self,
        parent,
        pedal_length: int,
        pedal_extend: int,
        pedal_size: tuple[int, int, int, int],
        raw_size: tuple[int, int, int, int],
        filtered_size: tuple[int, int, int, int],
        max_size: tuple[int, int, int, int],
        reading_size: tuple[int, int, int, int],
        fg_color: str = "",
        bg_color: str = "",
        input_color: str = "",
        ffb_color: str = "",
        show_reading: bool = False,
    ):
        super().__init__(parent)
        self.last = None
        self.input_color = input_color
        self.bg_color = bg_color
        self._is_maxed = False
        self._show_reading = show_reading
        self._input_reading = 0.0
        self._pedal_length = pedal_length
        self._pedal_extend = pedal_extend
        self._rect_pedal = QRectF(*pedal_size)
        self._rect_raw = QRectF(*raw_size)
        self._rect_filtered = QRectF(*filtered_size)
        self._rect_text = QRectF(*reading_size)
        self._pen = QPen()
        self._pen.setColor(fg_color)

        if ffb_color:
            self.rect_max = self._rect_pedal
            self.max_color = ffb_color
        else:
            self.rect_max = QRectF(*max_size)
            self.max_color = input_color

        self.setFixedSize(pedal_size[2], pedal_size[3])

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self._rect_pedal, self.bg_color)
        painter.fillRect(self._rect_raw, self.input_color)
        painter.fillRect(self._rect_filtered, self.input_color)
        if self._is_maxed:
            painter.fillRect(self.rect_max, self.max_color)
        if self._show_reading:
            painter.setPen(self._pen)
            painter.drawText(self._rect_text, Qt.AlignCenter, f"{self._input_reading:.0f}")


class VerticalPedalInputBar(_PedalInputBar):
    """Vertical pedal input bar"""

    def update_input(self, input_raw: float, input_filtered: float):
        """Update input value"""
        self._input_reading = max(input_raw, input_filtered) * 100
        self._is_maxed = input_raw >= 1
        scaled_raw = (1 - input_raw) * self._pedal_length + self._pedal_extend
        scaled_filtered = (1 - input_filtered) * self._pedal_length + self._pedal_extend
        self._rect_raw.setTop(scaled_raw)
        self._rect_filtered.setTop(scaled_filtered)
        self.update()


class HorizontalPedalInputBar(_PedalInputBar):
    """Horizontal pedal input bar"""

    def update_input(self, input_raw: float, input_filtered: float):
        """Update input value"""
        self._input_reading = max(input_raw, input_filtered) * 100
        self._is_maxed = input_raw >= 1
        scaled_raw = input_raw * self._pedal_length
        scaled_filtered = input_filtered * self._pedal_length
        self._rect_raw.setRight(scaled_raw)
        self._rect_filtered.setRight(scaled_filtered)
        self.update()


class ProgressBar(QWidget):
    """Progress bar"""

    def __init__(
        self,
        parent,
        font: QFont | None = None,
        text: str = "",
        width: int = 0,
        height: int = 0,
        offset_x: int = 0,
        offset_y: int = 0,
        input_color: str = "",
        fg_color: str = "",
        bg_color: str = "",
        show_reading: bool = False,
        alignment: str = "Center",
        right_side: bool = False,
    ):
        super().__init__(parent)
        if show_reading and font is not None:
            height = max(font.pixelSize(), height)
            self.setFont(font)

        if alignment == "Left":
            align = Qt.AlignLeft | Qt.AlignVCenter
        elif alignment == "Right":
            align = Qt.AlignRight | Qt.AlignVCenter
        else:
            align = Qt.AlignCenter

        self.last = -1
        self.text = text
        self.input_color = input_color
        self.bg_color = bg_color
        self.show_reading = show_reading
        self._bar_width = width
        self._rect_bar = QRectF(0, 0, width, height)
        self._rect_input = QRectF(0, 0, width, height)
        self._rect_text = QRectF(width * (offset_x - 0.5), offset_y, width, height)
        self._alignment = align
        self._right_side = right_side
        self._pen = QPen()
        self._pen.setColor(fg_color)

        self.setFixedSize(width, height)

    def update_input(self, input_value: float):
        """Update input"""
        if self._right_side:
            self._rect_input.setLeft((1 - input_value) * self._bar_width)
        else:
            self._rect_input.setRight(input_value * self._bar_width)
        self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self._rect_bar, self.bg_color)
        painter.fillRect(self._rect_input, self.input_color)
        if self.show_reading:
            painter.setPen(self._pen)
            painter.drawText(self._rect_text, self._alignment, self.text)


class FuelLevelBar(QWidget):
    """Fuel level bar"""

    def __init__(
        self,
        parent,
        width: int,
        height: int,
        start_mark_width: int,
        refill_mark_width: int,
        input_color: str = "",
        bg_color: str = "",
        start_mark_color: str = "",
        refill_mark_color: str = "",
        show_start_mark: bool = True,
        show_refill_mark: bool = True,
    ):
        super().__init__(parent)
        self.last = None
        self.input_color = input_color
        self.bg_color = bg_color
        self.start_mark_color = start_mark_color
        self.refill_mark_color = refill_mark_color
        self._bar_width = width
        self._rect_bar = QRectF(0, 0, width, height)
        self._rect_input = QRectF(0, 0, width, height)
        self._rect_start = QRectF(0, 0, start_mark_width, height)
        self._rect_refuel = QRectF(0, 0, refill_mark_width, height)
        self._show_start_mark = show_start_mark
        self._show_refill_mark = show_refill_mark

        self.setFixedSize(width, height)

    def update_input(self, input_value: float, start_value: float, refill_value: float):
        """Update input"""
        self._rect_input.setRight(input_value * self._bar_width)
        self._rect_start.moveLeft(start_value * self._bar_width)
        self._rect_refuel.moveLeft(refill_value * self._bar_width)
        self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self._rect_bar, self.bg_color)
        painter.fillRect(self._rect_input, self.input_color)
        if self._show_start_mark:
            painter.fillRect(self._rect_start, self.start_mark_color)
        if self._show_refill_mark:
            painter.fillRect(self._rect_refuel, self.refill_mark_color)


class GearGaugeBar(QWidget):
    """Gear gauge bar"""

    def __init__(
        self,
        parent,
        width: int,
        height: int,
        font_speed: QFont,
        gear_size: tuple[int, int, int, int],
        speed_size: tuple[int, int, int, int],
        fg_color: str,
        bg_color: str,
        show_speed: bool = True,
    ):
        super().__init__(parent)
        self.last = -1
        self._gear = "N"
        self._speed = 0
        self._color_index = 0
        self._show_speed = show_speed
        self._font_speed = font_speed
        self._bg_color = bg_color
        self._rect_gear = QRectF(*gear_size)
        self._rect_speed = QRectF(*speed_size)
        self._rect_bar = QRectF(0, 0, width, height)
        self._pen = QPen()
        self._pen.setColor(fg_color)

        self.setFixedSize(width, height)

    def update_input(self, gear: str, speed: int, color_index: int, bg_color: str):
        """Update input"""
        self._gear = gear
        self._speed = speed
        self._color_index = color_index
        self._bg_color = bg_color
        self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self._rect_bar, self._bg_color)
        if self._color_index == -4:  # flicker trigger
            return
        painter.setPen(self._pen)
        painter.drawText(self._rect_gear, Qt.AlignCenter, self._gear)
        if self._show_speed:
            painter.setFont(self._font_speed)
            painter.drawText(self._rect_speed, Qt.AlignCenter, f"{self._speed:03.0f}")


class RawText(QWidget):
    """Raw text widget for optimized drawing"""

    def __init__(
        self,
        parent,
        font: QFont | None = None,
        text: str = "",
        padding: int = 0,
        width: int = 0,
        height: int = 0,
        fixed_width: int = 0,
        fixed_height: int = 0,
        offset_y: int = 0,
        fg_color: str = "",
        bg_color: str = "",
        alignment: str = "Center",
        last: Any | None = None,
    ):
        super().__init__(parent)
        if font is not None:
            self.setFont(font)

        if alignment == "Left":
            align = Qt.AlignLeft | Qt.AlignVCenter
            padding_offset = padding
        elif alignment == "Right":
            align = Qt.AlignRight | Qt.AlignVCenter
            padding_offset = -padding
        else:
            align = Qt.AlignCenter
            padding_offset = 0

        if fixed_width > 0:
            self.setFixedWidth(fixed_width + padding * 2)
        elif width > 0:
            self.setMinimumWidth(width + padding * 2)

        if fixed_height > 0:
            self.setFixedHeight(fixed_height)
        elif height > 0:
            self.setMinimumHeight(height)

        self.state = None
        self.last = last
        self.text = text
        self.fg = fg_color if fg_color else Qt.transparent
        self.bg = bg_color if bg_color else Qt.transparent
        self._last_fg = ""
        self._alignment = align
        self._offset_x = padding_offset
        self._offset_y = offset_y
        self._pen_text = QPen()
        self._width = self.width()
        self._height = self.height()

    def clear(self):
        """Clear display"""
        self.text = ""
        self.fg = Qt.transparent
        self.bg = Qt.transparent

    def resizeEvent(self, event):
        """Update size info"""
        self._width = self.width()
        self._height = self.height()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        if self._last_fg != self.fg:
            self._last_fg = self.fg  # avoid calling re-set color if same
            self._pen_text.setColor(self.fg)
        painter.setPen(self._pen_text)
        painter.fillRect(0, 0, self._width, self._height, self.bg)
        painter.drawText(self._offset_x, self._offset_y, self._width, self._height, self._alignment, self.text)


class RawImage(QWidget):
    """Raw image widget for optimized drawing"""

    def __init__(
        self,
        parent,
        image: QPixmap | None = None,
        width: int = 0,
        height: int = 0,
        fixed_width: int = 0,
        fixed_height: int = 0,
        bg_color: str = "",
        last: Any | None = None,
    ):
        super().__init__(parent)
        if fixed_width > 0:
            self.setFixedWidth(fixed_width)
        elif width > 0:
            self.setMinimumWidth(width)

        if fixed_height > 0:
            self.setFixedHeight(fixed_height)
        elif height > 0:
            self.setMinimumHeight(height)

        self.state = None
        self.last = last
        self.image = image
        self.bg = bg_color if bg_color else Qt.transparent
        self._width = self.width()
        self._height = self.height()

    def clear(self):
        """Clear display"""
        self.image = None
        self.bg = Qt.transparent

    def resizeEvent(self, event):
        """Update size info"""
        self._width = self.width()
        self._height = self.height()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(0, 0, self._width, self._height, self.bg)
        if isinstance(self.image, QPixmap):
            painter.drawPixmap(
                (self._width - self.image.width()) // 2,  # align center
                (self._height - self.image.height()) // 2,
                self.image,
            )


class MultiCompounds(QWidget):
    """Multi color compounds text"""

    def __init__(
        self,
        parent,
        font: QFont | None = None,
        count: int = 4,
        spacing: int = 0,
        padding: int = 0,
        width: int = 0,
        height: int = 0,
        offset_y: int = 0,
        fg_color: str = "",
        bg_color: str = "",
        last: Any | None = None,
    ):
        super().__init__(parent)
        if font is not None:
            self.setFont(font)

        self.setMinimumWidth(count * (width + spacing) + padding * 2)
        self.setFixedHeight(height)

        self.state = None
        self.last = last
        fg = fg_color if fg_color else Qt.transparent
        self.bg = bg_color if bg_color else Qt.transparent
        self.compounds = ()
        self.colors = (fg,) * count
        self._count = count
        self._offset_y = offset_y
        self._word_width = width + spacing
        self._pen_text = QPen()
        self._width = self.width()
        self._height = self.height()

    def clear(self):
        """Clear display"""
        self.compounds = ()
        self.colors = (Qt.transparent,) * self._count
        self.bg = Qt.transparent

    def resizeEvent(self, event):
        """Update size info"""
        self._width = self.width()
        self._height = self.height()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(0, 0, self._width, self._height, self.bg)
        if not self.compounds:
            return
        # Recalculate padding in case width increased
        padding = (self._width - self._count * self._word_width) // 2
        for index, compound in enumerate(self.compounds):
            if compound == "":
                continue
            self._pen_text.setColor(self.colors[index])
            painter.setPen(self._pen_text)
            painter.drawText(
                padding + self._word_width * index,
                self._offset_y,
                self._word_width,
                self._height,
                Qt.AlignCenter,
                compound,
            )


class DeltaLapTime(QWidget):
    """Delta lap time text"""

    def __init__(
        self,
        parent,
        font: QFont | None = None,
        count: int = 5,
        spacing: int = 0,
        padding: int = 0,
        width: int = 0,
        height: int = 0,
        offset_y: int = 0,
        fg_color: str = "",
        bg_color: str = "",
        fg_color_gain: str = "",
        fg_color_loss: str = "",
        fg_color_player: str = "",
        inverted: bool = False,
        last: Any | None = None,
    ):
        super().__init__(parent)
        if font is not None:
            self.setFont(font)

        self.setMinimumWidth(count * (width + spacing) + padding * 2)
        self.setFixedHeight(height)

        self.state = None
        self.last = last
        self.fg = fg_color if fg_color else Qt.transparent
        self.bg = bg_color if bg_color else Qt.transparent
        self.fg_gain = fg_color_gain
        self.fg_loss = fg_color_loss
        self.fg_player = fg_color_player
        self.delta = ()
        self.is_player = False
        self._count = count
        self._offset_y = offset_y
        self._padding = padding
        self._word_width = width + spacing
        self._pen_text = QPen()
        self._width = self.width()
        self._height = self.height()
        self._inverted = inverted

    def clear(self):
        """Clear display"""
        self.delta = ()
        self.bg = Qt.transparent
        self.is_player = False

    def resizeEvent(self, event):
        """Update size info"""
        self._width = self.width()
        self._height = self.height()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(0, 0, self._width, self._height, self.bg)
        if not self.delta:
            return
        # Recalculate padding in case width increased
        padding = (self._width - self._count * self._word_width) // 2
        for index, delta in enumerate(
            reversed(self.delta) if self._inverted else self.delta
        ):
            if delta == "":
                continue

            if -999 < delta < 0:  # player time gain
                if delta < -9.94:
                    text = f"{-delta:.0f}"
                else:
                    text = f"{-delta:.1f}"
                fg_color = self.fg_gain
            elif 0 < delta < 999:  # player time loss
                if delta > 9.94:
                    text = f"{delta:.0f}"
                else:
                    text = f"{delta:.1f}"
                fg_color = self.fg_loss
            elif delta == 0:
                text = "0.0"
                fg_color = self.fg
            else:
                text = "-.-"
                fg_color = self.fg

            if self.is_player:
                fg_color = self.fg_player

            self._pen_text.setColor(fg_color)
            painter.setPen(self._pen_text)
            painter.drawText(
                padding + self._word_width * index,
                self._offset_y,
                self._word_width,
                self._height,
                Qt.AlignCenter,
                text,
            )
