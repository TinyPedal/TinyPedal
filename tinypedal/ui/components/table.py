from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QWidget

DEFAULT_ROW_HEIGHT = 24


class OptionTable(QWidget):
    """
    Table view for configuration options.
    Contains an optional title and rows with label and editor.
    Rows have alternating background colors.
    """

    rowClicked = Signal(str)  # emits the key of the clicked row

    def __init__(self, parent=None, columns=1, row_height=DEFAULT_ROW_HEIGHT):
        super().__init__(parent)
        self._columns = columns
        self._row_height = row_height
        self._keys = []  # keys in order of addition
        self._row_widgets = {}  # key -> row widget
        self._row_labels = {}   # key -> label widget
        self._title_label = None

        self._extra_rows = 0  # non-key rows (section headers)
        self._section_headers = []  # section header labels

        self._layout = QGridLayout(self)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def set_title(self, title: str):
        """Add a title to the table (top row, spanning all columns)."""
        if self._title_label is None:
            self._title_label = QLabel(f"<b>{title}</b>")
            font = self._title_label.font()
            font.setPointSize(font.pointSize() + 1)
            self._title_label.setFont(font)
            self._title_label.setStyleSheet("""
                background-color: palette(dark);
                color: palette(bright-text);
                border-bottom: 2px solid palette(mid);
                padding: 4px;
            """)
            self._layout.addWidget(self._title_label, 0, 0, 1, self._columns * 2)
        else:
            self._title_label.setText(f"<b>{title}</b>")

    def add_section_header(self, title: str):
        """Add a section sub-header spanning all columns."""
        row_index = len(self._keys) + self._extra_rows
        if self._title_label is not None:
            row_index += 1
        grid_row = row_index // self._columns

        label = QLabel(f"<b>{title}</b>")
        font = label.font()
        font.setPointSize(font.pointSize() + 1)
        label.setFont(font)
        label.setStyleSheet(self._TITLE_STYLE_NORMAL)

        self._layout.addWidget(label, grid_row, 0, 1, self._columns * 2)
        self._section_headers.append(label)
        self._extra_rows += 1

    def add_row(self, key: str, label_text: str, editor: QWidget):
        """
        Add a new row to the table.
        - key: unique identifier (e.g. config key)
        - label_text: text for the label
        - editor: the editor widget (QCheckBox, QComboBox, QLineEdit, etc.)
        """
        row_index = len(self._keys) + self._extra_rows
        if self._title_label is not None:
            row_index += 1  # title occupies row 0

        col_offset = (row_index % self._columns) * 2
        grid_row = row_index // self._columns

        row_widget = QWidget()
        row_widget.setFixedHeight(self._row_height)
        bg = "palette(alternate-base)" if (grid_row % 2 == 0) else "palette(base)"
        row_widget.setStyleSheet(f"background-color: {bg};")
        row_widget.setProperty("_base_bg", bg)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(4, 1, 4, 1)
        row_layout.setSpacing(4)

        label = QLabel(label_text)
        label.setCursor(Qt.PointingHandCursor)
        label.setStyleSheet("""
            QLabel:hover {
                background-color: rgba(0, 120, 215, 0.2);
            }
        """)
        row_layout.addWidget(label)

        row_layout.addWidget(editor)

        self._layout.addWidget(row_widget, grid_row, col_offset, 1, 2)

        self._keys.append(key)
        self._row_widgets[key] = row_widget
        self._row_labels[key] = label

        label.mousePressEvent = lambda event, k=key: self._on_row_click(k, event)

    def _on_row_click(self, key, event):
        """Handle click on row label."""
        if event.button() == Qt.LeftButton:
            self.rowClicked.emit(key)

    def row_widget(self, key: str) -> QWidget:
        """Return the container widget of a row."""
        return self._row_widgets.get(key)

    def row_label(self, key: str) -> QLabel:
        """Return the label widget of a row."""
        return self._row_labels.get(key)

    def keys(self) -> list:
        """Return the list of keys in current order."""
        return self._keys[:]

    def clear(self):
        """Remove all rows (keep title if present)."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self._title_label:
                widget.deleteLater()
        self._keys.clear()
        self._row_widgets.clear()
        self._row_labels.clear()
        self._section_headers.clear()
        self._extra_rows = 0
        if self._title_label is not None:
            self._layout.addWidget(self._title_label, 0, 0, 1, self._columns * 2)

    def estimated_rows(self) -> int:
        """Estimated number of rows (including title and section headers) for layout distribution."""
        total = len(self._keys) + self._extra_rows
        rows = total // self._columns + (1 if total % self._columns else 0)
        if self._title_label is not None:
            rows += 1
        return rows

    @property
    def title_label(self):
        """Public access to the title label."""
        return self._title_label

    # ------------------------------------------------------------------
    # Filter / highlight
    # ------------------------------------------------------------------
    _TITLE_STYLE_NORMAL = """
        background-color: palette(dark);
        color: palette(bright-text);
        border-bottom: 2px solid palette(mid);
        padding: 4px;
    """
    _TITLE_STYLE_DIMMED = """
        background-color: palette(mid);
        color: palette(window);
        border-bottom: 2px solid palette(mid);
        padding: 4px;
    """

    def apply_filter(self, text: str):
        """Dim rows that don't match the filter text, undim those that do."""
        if not text:
            for key in self._keys:
                self._undim_row(key)
            if self._title_label is not None:
                self._title_label.setStyleSheet(self._TITLE_STYLE_NORMAL)
            return

        all_dimmed = True
        for key in self._keys:
            if text in key.lower():
                self._undim_row(key)
                all_dimmed = False
            else:
                self._dim_row(key)

        if self._title_label is not None:
            style = self._TITLE_STYLE_DIMMED if all_dimmed else self._TITLE_STYLE_NORMAL
            self._title_label.setStyleSheet(style)

    def highlight_keys(self, keys: set[str]):
        """Highlight rows matching the given keys."""
        for key in keys:
            row = self._row_widgets.get(key)
            if row:
                row.setStyleSheet("background-color: lightblue;")

    def clear_highlight(self, keys: set[str]):
        """Reset highlighted rows back to their base color."""
        for key in keys:
            row = self._row_widgets.get(key)
            if row:
                bg = row.property("_base_bg") or "palette(base)"
                row.setStyleSheet(f"background-color: {bg};")

    def _dim_row(self, key: str):
        row = self._row_widgets.get(key)
        label = self._row_labels.get(key)
        if row is None:
            return
        row.setStyleSheet("background-color: palette(window);")
        if label is not None:
            label.setStyleSheet("color: palette(mid);")

    def _undim_row(self, key: str):
        row = self._row_widgets.get(key)
        label = self._row_labels.get(key)
        if row is None:
            return
        bg = row.property("_base_bg") or "palette(base)"
        row.setStyleSheet(f"background-color: {bg};")
        if label is not None:
            label.setStyleSheet("")
