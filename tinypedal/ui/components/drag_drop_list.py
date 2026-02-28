from PySide2.QtCore import Qt, QMimeData, QEvent, Signal
from PySide2.QtGui import QDrag, QPixmap, QMouseEvent
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

DEFAULT_ROW_HEIGHT = 24


class DragHandle(QLabel):
    """Handle used to drag a row."""
    def __init__(self, parent=None):
        super().__init__(" ⋮⋮ ", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(20)
        self.setStyleSheet("background-color: palette(mid); color: palette(text);")
        self.setCursor(Qt.OpenHandCursor)

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)


class OrderRow(QWidget):
    """Single row: number (static), text (clickable for highlight), handle (draggable)."""
    def __init__(self, key: str, label: str, row_height: int, parent=None):
        super().__init__(parent)
        self.key = key
        self.label = label
        self.setFixedHeight(row_height)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Number label
        self.number_label = QLabel()
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setFixedWidth(row_height)
        self.number_label.setContentsMargins(0, 0, 0, 0)
        self.number_label.setCursor(Qt.PointingHandCursor)
        self.number_label.setStyleSheet("""
            QLabel:hover {
                background-color: rgba(0, 120, 215, 0.2);
            }
        """)

        # Text label
        self.text_label = QLabel(label)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setIndent(5)
        self.text_label.setFixedHeight(row_height)
        self.text_label.setContentsMargins(0, 0, 0, 0)
        self.text_label.setCursor(Qt.PointingHandCursor)
        self.text_label.setStyleSheet("""
            QLabel:hover {
                background-color: rgba(0, 120, 215, 0.2);
            }
        """)

        self.drag_handle = DragHandle(self)
        self.drag_handle.setFixedHeight(row_height)

        layout.addWidget(self.number_label)
        layout.addWidget(self.text_label, 1)
        layout.addWidget(self.drag_handle)
        self.setLayout(layout)

    def set_number(self, number: int):
        self.number_label.setText(str(number))

class DragDropOrderList(QWidget):
    """Container with drag & drop list. Emits sectionClicked(key) on text/number click."""
    sectionClicked = Signal(str)  # emits the key of the clicked row

    def __init__(self, items: list[tuple[str, str]], on_reorder_callback,
                 row_height: int = DEFAULT_ROW_HEIGHT, parent=None):
        super().__init__(parent)
        self._callback = on_reorder_callback
        self._row_height = row_height
        self._all_items = items[:]  # keep for reset
        self.setAcceptDrops(True)

        self.drop_indicator = QFrame()
        self.drop_indicator.setFixedHeight(2)
        self.drop_indicator.setStyleSheet("background-color: blue;")
        self.drop_indicator.hide()

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        for key, label in items:
            self._add_row(key, label)

        self._update_row_numbers()
        self._update_row_colors()

    def _add_row(self, key: str, label: str):
        row = OrderRow(key, label, self._row_height, self)
        self.layout.addWidget(row)
        row.number_label.installEventFilter(self)
        row.text_label.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            mouse_event = QMouseEvent(event)
            if mouse_event.button() == Qt.LeftButton:
                parent_row = obj.parent()
                if isinstance(parent_row, OrderRow):
                    self.sectionClicked.emit(parent_row.key)
        return super().eventFilter(obj, event)

    def dragEnterEvent(self, e):
        if isinstance(e.source(), DragHandle):
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if not isinstance(e.source(), DragHandle):
            e.ignore()
            return

        if self.drop_indicator.parent() == self:
            self.layout.removeWidget(self.drop_indicator)
            self.drop_indicator.hide()

        pos = e.pos()
        n = 0
        while n < self.layout.count():
            w = self.layout.itemAt(n).widget()
            if pos.y() < w.y() + w.height() // 2:
                break
            n += 1

        self.layout.insertWidget(n, self.drop_indicator)
        self.drop_indicator.show()
        e.accept()

    def dragLeaveEvent(self, e):
        if self.drop_indicator.parent() == self:
            self.layout.removeWidget(self.drop_indicator)
            self.drop_indicator.hide()
        e.accept()

    def dropEvent(self, e):
        source_handle = e.source()
        if not isinstance(source_handle, DragHandle):
            return

        if self.drop_indicator.parent() == self:
            self.layout.removeWidget(self.drop_indicator)
            self.drop_indicator.hide()

        source_row = source_handle.parent()
        if not isinstance(source_row, OrderRow):
            return

        self.layout.removeWidget(source_row)

        pos = e.pos()
        n = 0
        while n < self.layout.count():
            w = self.layout.itemAt(n).widget()
            if pos.y() < w.y() + w.height() // 2:
                break
            n += 1

        self.layout.insertWidget(n, source_row)
        e.accept()

        self._update_row_numbers()
        self._update_row_colors()
        self._emit_reorder()

    def _update_row_numbers(self):
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, OrderRow):
                w.set_number(i + 1)

    def _update_row_colors(self):
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, OrderRow):
                if i % 2 == 0:
                    w.setStyleSheet("background-color: palette(alternate-base);")
                else:
                    w.setStyleSheet("background-color: palette(base);")

    def _emit_reorder(self):
        if self._callback:
            keys = []
            for i in range(self.layout.count()):
                w = self.layout.itemAt(i).widget()
                if isinstance(w, OrderRow):
                    keys.append(w.key)
            self._callback(keys)

    def apply_filter(self, text: str):
        """Dim rows that don't match the filter text."""
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, OrderRow):
                if not text or text in w.key.lower():
                    bg = "palette(alternate-base)" if i % 2 == 0 else "palette(base)"
                    w.setStyleSheet(f"background-color: {bg};")
                    w.number_label.setStyleSheet("")
                    w.text_label.setStyleSheet("")
                else:
                    w.setStyleSheet("background-color: palette(window);")
                    w.number_label.setStyleSheet("color: palette(mid);")
                    w.text_label.setStyleSheet("color: palette(mid);")

    def reset_to_defaults(self, default_values: dict):
        """Reset the order to default values."""
        sorted_items = sorted(self._all_items, key=lambda item: default_values.get(item[0], 999))
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, OrderRow):
                w.setParent(None)
                w.deleteLater()
        for key, label in sorted_items:
            self._add_row(key, label)
        self._update_row_numbers()
        self._update_row_colors()
