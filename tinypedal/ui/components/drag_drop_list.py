"""Drag-and-drop reorderable list widget"""

from PySide2.QtCore import Qt, QMimeData, Signal
from PySide2.QtGui import QDrag, QPixmap
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

from .base import BaseComponent


class ClickableLabel(QLabel):
    """Label that emits clicked on left mouse press"""
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DragHandle(QLabel):
    """Drag handle for reordering rows"""

    def __init__(self, text=" \u22ee\u22ee ", width=20, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(width)
        self.setCursor(Qt.OpenHandCursor)
        self.setStyleSheet("background-color: palette(mid); color: palette(text);")

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec_(Qt.MoveAction)


class OrderRow(QWidget):
    """Row with number, label, and drag handle"""
    clicked = Signal()

    def __init__(self, key, label, row_height, parent=None):
        super().__init__(parent)
        self.key = key
        self.label_text = label
        self.setFixedHeight(row_height)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Number
        self.number_label = ClickableLabel()
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setFixedWidth(row_height)
        self.number_label.setCursor(Qt.PointingHandCursor)
        self.number_label.setStyleSheet(
            "ClickableLabel:hover { background-color: rgba(0, 120, 215, 0.2); }")
        self.number_label.clicked.connect(self.clicked)
        # Text
        self.text_label = ClickableLabel(label)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setIndent(5)
        self.text_label.setFixedHeight(row_height)
        self.text_label.setCursor(Qt.PointingHandCursor)
        self.text_label.setStyleSheet(
            "ClickableLabel:hover { background-color: rgba(0, 120, 215, 0.2); }")
        self.text_label.clicked.connect(self.clicked)
        # Drag handle
        self.drag_handle = DragHandle(parent=self)
        layout.addWidget(self.number_label)
        layout.addWidget(self.text_label, 1)
        layout.addWidget(self.drag_handle)

    def set_number(self, number):
        self.number_label.setText(str(number))

    def set_base_bg(self, bg):
        self._base_bg = bg
        self.setStyleSheet(f"background-color: {bg};")

    def set_dimmed(self, dimmed):
        if dimmed:
            self.setStyleSheet("background-color: palette(window);")
            self.number_label.setStyleSheet("color: palette(mid);")
            self.text_label.setStyleSheet("color: palette(mid);")
        else:
            bg = getattr(self, "_base_bg", "palette(base)")
            self.setStyleSheet(f"background-color: {bg};")
            self.number_label.setStyleSheet("")
            self.text_label.setStyleSheet("")


class DragDropOrderList(BaseComponent):
    """Reorderable list with drag-and-drop"""

    itemClicked = Signal(str)
    orderChanged = Signal(list)

    def __init__(self, items, row_height=24, parent=None):
        super().__init__(parent)
        self._row_height = row_height
        self._original_items = items[:]
        self._items = items[:]
        self._filter_text = ""
        self._title_widget = None
        self.setAcceptDrops(True)
        # Drop indicator
        self._drop_indicator = QFrame()
        self._drop_indicator.setFixedHeight(2)
        self._drop_indicator.setStyleSheet("background-color: blue;")
        self._drop_indicator.hide()
        # Layout
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._rebuild_rows()

    def set_title(self, title):
        """Add a styled header above the list"""
        if self._title_widget:
            self._title_widget.deleteLater()
        header = QLabel(f"<b>{title}</b>")
        font = header.font()
        font.setPointSize(font.pointSize() + 1)
        header.setFont(font)
        header.setStyleSheet(
            "background-color: palette(dark);"
            "color: palette(bright-text);"
            "border-bottom: 2px solid palette(mid);"
            "padding: 4px;"
        )
        self._layout.insertWidget(0, header)
        self._title_widget = header

    def _rebuild_rows(self):
        # Preserve title if any
        title = self._title_widget
        if title:
            self._layout.removeWidget(title)
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if title:
            self._layout.addWidget(title)
        for key, label in self._items:
            row = OrderRow(key, label, self._row_height, self)
            row.clicked.connect(lambda k=key: self.itemClicked.emit(k))
            self._layout.addWidget(row)
        self._update_row_numbers()
        self._update_row_colors()
        self._apply_filter_to_rows()

    def _update_row_numbers(self):
        for i, row in enumerate(self._rows()):
            row.set_number(i + 1)

    def _update_row_colors(self):
        for i, row in enumerate(self._rows()):
            bg = "palette(alternate-base)" if i % 2 == 0 else "palette(base)"
            row.set_base_bg(bg)

    def _rows(self):
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if isinstance(w, OrderRow):
                yield w

    # Drag & drop
    def dragEnterEvent(self, event):
        if isinstance(event.source(), DragHandle):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not isinstance(event.source(), DragHandle):
            event.ignore()
            return
        self._hide_indicator()
        insert_index = self._find_insert_index(event.pos())
        self._layout.insertWidget(insert_index, self._drop_indicator)
        self._drop_indicator.show()
        event.accept()

    def dragLeaveEvent(self, event):
        self._hide_indicator()
        event.accept()

    def dropEvent(self, event):
        source_handle = event.source()
        if not isinstance(source_handle, DragHandle):
            return
        source_row = source_handle.parent()
        if not isinstance(source_row, OrderRow):
            return
        self._hide_indicator()
        self._layout.removeWidget(source_row)
        insert_index = self._find_insert_index(event.pos())
        self._layout.insertWidget(insert_index, source_row)
        event.accept()
        self._update_model_from_layout()
        self._update_row_numbers()
        self._update_row_colors()
        self.orderChanged.emit([row.key for row in self._rows()])

    def _find_insert_index(self, pos):
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w and w.isVisible() and pos.y() < w.y() + w.height() // 2:
                return i
        return self._layout.count()

    def _hide_indicator(self):
        if self._drop_indicator.parent() == self:
            self._layout.removeWidget(self._drop_indicator)
            self._drop_indicator.hide()

    def _update_model_from_layout(self):
        self._items = [(row.key, row.label_text) for row in self._rows()]

    # Filter
    def apply_filter(self, text):
        self._filter_text = text.strip().lower()
        self._apply_filter_to_rows()

    def _apply_filter_to_rows(self):
        for row in self._rows():
            matches = not self._filter_text or self._filter_text in row.key.lower()
            row.set_dimmed(not matches)

    # Reset
    def reset_to_defaults(self, default_order):
        """Reset list to default order"""
        self._items = sorted(
            self._original_items,
            key=lambda item: default_order.get(item[0], 999)
        )
        self._rebuild_rows()
        self.orderChanged.emit([key for key, _ in self._items])

    def keys(self):
        return [row.key for row in self._rows()]
