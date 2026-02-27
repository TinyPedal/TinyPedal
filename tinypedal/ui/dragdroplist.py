"""Drag-and-drop reorderable list widget for display order settings"""

from PySide2.QtCore import Qt, QMimeData
from PySide2.QtGui import QDrag, QPixmap
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

DEFAULT_ROW_HEIGHT = 24


class DraggableLabel(QLabel):
    """Label that initiates a drag operation on mouse move"""

    def __init__(self, key: str, text: str, parent=None):
        super().__init__(text, parent)
        self.key = key
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setIndent(5)

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
    """Single row: static number label + draggable text label"""

    def __init__(self, key: str, label: str, row_height: int, parent=None):
        super().__init__(parent)
        self.key = key
        self.setFixedHeight(row_height)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Number (static, square)
        self.number_label = QLabel()
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setFixedWidth(row_height)
        self.number_label.setContentsMargins(0, 0, 0, 0)

        # Draggable label (shows the text)
        self.drag_label = DraggableLabel(key, label, self)
        self.drag_label.setFixedHeight(row_height)
        self.drag_label.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.number_label)
        layout.addWidget(self.drag_label, 1)
        self.setLayout(layout)

    def set_number(self, number: int):
        """Set the row number displayed on the left"""
        self.number_label.setText(str(number))


class DragDropOrderList(QWidget):
    """Container that handles drag-and-drop reordering and fires a callback"""

    def __init__(self, items: list[tuple[str, str]], on_reorder_callback,
                 row_height: int = DEFAULT_ROW_HEIGHT, parent=None):
        """
        Parameters
        ----------
        items : list of (key, label) tuples
        on_reorder_callback : callable receiving a list of keys
        row_height : fixed height per row (pixels)
        """
        super().__init__(parent)

        self._callback = on_reorder_callback
        self._row_height = row_height
        self._dimmed_keys: set[str] = set()
        self.setAcceptDrops(True)

        # Drop indicator line (shown between rows during drag)
        self._drop_indicator = QFrame(self)
        self._drop_indicator.setFixedHeight(2)
        self._drop_indicator.setStyleSheet("background-color: palette(highlight);")
        self._drop_indicator.hide()

        # Rows whose number labels are currently highlighted during drag
        self._highlighted_rows: list[OrderRow] = []

        # Main layout
        box = QVBoxLayout()
        box.setSpacing(0)
        box.setContentsMargins(0, 0, 0, 0)
        self.setLayout(box)

        for key, label in items:
            self._add_row(key, label)

        self._update_row_numbers()
        self._update_row_colors()

    # ------------------------------------------------------------------
    #  Row helpers
    # ------------------------------------------------------------------

    def _add_row(self, key: str, label: str):
        """Append a new row at the end"""
        row = OrderRow(key, label, self._row_height, self)
        self.layout().addWidget(row)

    def _find_insert_index(self, pos):
        """Return layout index where a row should be inserted for *pos*"""
        box = self.layout()
        n = 0
        while n < box.count():
            w = box.itemAt(n).widget()
            if w is not None and pos.y() < w.y() + w.height() // 2:
                break
            n += 1
        return n

    # ------------------------------------------------------------------
    #  Drag-and-drop events
    # ------------------------------------------------------------------

    def dragEnterEvent(self, e):
        e.accept()

    def dragMoveEvent(self, e):
        source_label = e.source()
        if not isinstance(source_label, DraggableLabel):
            e.ignore()
            return

        box = self.layout()

        # Remove indicator if still in the layout
        if self._drop_indicator.parent() == self:
            box.removeWidget(self._drop_indicator)
            self._drop_indicator.hide()

        # Insert indicator at calculated position
        n = self._find_insert_index(e.pos())
        box.insertWidget(n, self._drop_indicator)
        self._drop_indicator.show()

        # Highlight number labels on adjacent rows
        self._clear_highlight()
        for offset in (n - 1, n + 1):
            if 0 <= offset < box.count():
                row = box.itemAt(offset).widget()
                if isinstance(row, OrderRow):
                    row.number_label.setStyleSheet(
                        "background-color: palette(highlight);"
                        "color: palette(highlighted-text);"
                    )
                    self._highlighted_rows.append(row)

        e.accept()

    def dragLeaveEvent(self, e):
        self._clear_highlight()
        if self._drop_indicator.parent() == self:
            self.layout().removeWidget(self._drop_indicator)
            self._drop_indicator.hide()
        e.accept()

    def dropEvent(self, e):
        source_label = e.source()
        if not isinstance(source_label, DraggableLabel):
            return

        self._clear_highlight()

        box = self.layout()

        # Remove the drop indicator
        if self._drop_indicator.parent() == self:
            box.removeWidget(self._drop_indicator)
            self._drop_indicator.hide()

        source_row = source_label.parent()
        if not isinstance(source_row, OrderRow):
            return

        # Remove row, calculate new position, re-insert
        box.removeWidget(source_row)
        n = self._find_insert_index(e.pos())
        box.insertWidget(n, source_row)
        e.accept()

        self._update_row_numbers()
        self._update_row_colors()
        self._emit_reorder()

    # ------------------------------------------------------------------
    #  Visual updates
    # ------------------------------------------------------------------

    def _clear_highlight(self):
        """Remove highlight styling from any previously highlighted number labels"""
        for row in self._highlighted_rows:
            row.number_label.setStyleSheet("")
        self._highlighted_rows.clear()

    def _update_row_numbers(self):
        """Set row numbers (1-based) according to current order"""
        num = 1
        box = self.layout()
        for i in range(box.count()):
            row = box.itemAt(i).widget()
            if isinstance(row, OrderRow):
                row.set_number(num)
                num += 1

    def _update_row_colors(self):
        """Apply alternating row background colors, with dimming for filtered rows"""
        num = 0
        box = self.layout()
        for i in range(box.count()):
            row = box.itemAt(i).widget()
            if isinstance(row, OrderRow):
                if row.key in self._dimmed_keys:
                    row.setStyleSheet("background-color: palette(window);")
                    row.drag_label.setStyleSheet("color: palette(mid);")
                    row.number_label.setStyleSheet("color: palette(mid);")
                else:
                    if num % 2 == 0:
                        row.setStyleSheet("background-color: palette(alternate-base);")
                    else:
                        row.setStyleSheet("background-color: palette(base);")
                    row.drag_label.setStyleSheet("")
                    row.number_label.setStyleSheet("")
                num += 1

    def _emit_reorder(self):
        """Collect current key order and invoke the callback"""
        if self._callback:
            keys = []
            box = self.layout()
            for i in range(box.count()):
                row = box.itemAt(i).widget()
                if isinstance(row, OrderRow):
                    keys.append(row.key)
            self._callback(keys)

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def get_key_order(self):
        """Return the current list of keys in display order"""
        keys = []
        box = self.layout()
        for i in range(box.count()):
            row = box.itemAt(i).widget()
            if isinstance(row, OrderRow):
                keys.append(row.key)
        return keys

    def set_dimmed_keys(self, keys: set[str]):
        """Update which keys are dimmed and refresh row colors"""
        self._dimmed_keys = keys
        self._update_row_colors()

    def reset_to_defaults(self, default_values: dict):
        """Re-sort rows to match *default_values* ordering"""
        box = self.layout()

        # Collect all OrderRow widgets
        rows = []
        for i in range(box.count()):
            row = box.itemAt(i).widget()
            if isinstance(row, OrderRow):
                rows.append(row)

        # Remove from layout (without deleting)
        for row in rows:
            box.removeWidget(row)

        # Re-insert sorted by default value
        rows.sort(key=lambda r: default_values.get(r.key, 999))
        for row in rows:
            box.addWidget(row)

        self._update_row_numbers()
        self._update_row_colors()
        self._emit_reorder()
