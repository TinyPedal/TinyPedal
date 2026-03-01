"""Option table widget for config dialog"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget

from .base import BaseComponent


class OptionTable(BaseComponent):
    """Table with label-editor rows and optional title"""

    def __init__(self, parent=None, columns=1, row_height=24, editor_width=0,
                 padding=(4, 1, 4, 1), label_alignment=Qt.AlignLeft | Qt.AlignVCenter):
        super().__init__(parent)
        self._columns = columns
        self._row_height = row_height
        self._editor_width = editor_width
        self._padding = padding
        self._label_alignment = label_alignment
        self._keys = []
        self._row_widgets = {}
        self._row_labels = {}
        self._title_label = None
        self._extra_rows = 0
        self._section_headers = []
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._layout = QGridLayout(self)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def set_title(self, title):
        if self._title_label is None:
            self._title_label = QLabel(f"<b>{title}</b>")
            self._title_label.setObjectName("sectionTitle")
            font = self._title_label.font()
            font.setPointSize(font.pointSize() + 1)
            self._title_label.setFont(font)
            self._layout.addWidget(self._title_label, 0, 0, 1, self._columns * 2)
        else:
            self._title_label.setText(f"<b>{title}</b>")

    def add_section_header(self, title):
        """Add a section sub-header spanning all columns"""
        row_index = len(self._keys) + self._extra_rows
        if self._title_label is not None:
            row_index += self._columns
        grid_row = row_index // self._columns
        label = QLabel(f"<b>{title}</b>")
        label.setObjectName("sectionTitle")
        font = label.font()
        font.setPointSize(font.pointSize() + 1)
        label.setFont(font)
        self._layout.addWidget(label, grid_row, 0, 1, self._columns * 2)
        self._section_headers.append(label)
        self._extra_rows += self._columns

    def add_row(self, key, label_text, editor):
        """Add a label-editor row"""
        row_index = len(self._keys) + self._extra_rows
        if self._title_label is not None:
            row_index += self._columns
        col_offset = (row_index % self._columns) * 2
        grid_row = row_index // self._columns
        # Row container
        row_widget = QWidget()
        row_widget.setFixedHeight(self._row_height)
        bg = "palette(alternate-base)" if (grid_row % 2 == 0) else "palette(base)"
        row_widget.setStyleSheet(f"background-color: {bg};")
        row_widget.setProperty("_base_bg", bg)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(*self._padding)
        row_layout.setSpacing(self._padding[0])
        # Label — stretches left
        label = QLabel(label_text)
        label.setAlignment(self._label_alignment)
        label.setCursor(Qt.PointingHandCursor)
        row_layout.addWidget(label, 1)
        # Editor — fixed right, vertically centered
        if self._editor_width:
            editor.setFixedWidth(self._editor_width)
        row_layout.addWidget(editor, 0, Qt.AlignRight | Qt.AlignVCenter)
        self._layout.addWidget(row_widget, grid_row, col_offset, 1, 2)
        self._keys.append(key)
        self._row_widgets[key] = row_widget
        self._row_labels[key] = label

    def row_widget(self, key):
        return self._row_widgets.get(key)

    def row_label(self, key):
        return self._row_labels.get(key)

    def keys(self):
        return self._keys[:]

    @property
    def title_label(self):
        return self._title_label

