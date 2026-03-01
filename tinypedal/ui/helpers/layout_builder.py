"""Layout builder for vertical row stacking"""

from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget


class ColumnsRow(QWidget):
    """Dynamic grid that reflows columns on resize"""

    def __init__(self, widgets=None, max_columns=5, spacing=0, parent=None):
        super().__init__(parent)
        self._max_columns = max_columns
        self._widgets = []
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(spacing)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._reflow)
        if widgets:
            self.setWidgets(widgets)

    def setWidgets(self, widgets):
        """Replace child widgets (not deleted, ownership stays with caller)"""
        self._clear_layout()
        self._widgets = list(widgets)
        self._reflow()

    def _reflow(self):
        """Recompute columns and rearrange widgets"""
        # Filter deleted widgets
        alive = []
        for w in self._widgets:
            try:
                w.sizeHint()
                alive.append(w)
            except RuntimeError:
                pass
        self._widgets = alive

        if not self._widgets:
            self.updateGeometry()
            return

        avail_width = self.width()
        if avail_width <= 0:
            parent = self.parent()
            avail_width = parent.width() if parent else 800

        widest = max((w.sizeHint().width() for w in self._widgets), default=1)
        num_cols = max(1, min(self._max_columns, avail_width // max(widest, 1)))

        self._clear_layout()
        for idx, w in enumerate(self._widgets):
            self._grid.addWidget(w, idx // num_cols, idx % num_cols, Qt.AlignTop)
            w.show()
        self.updateGeometry()

    def _clear_layout(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(50)


class LayoutBuilder:
    """Builds a vertical stack of rows"""

    def __init__(self, spacing=2, column_spacing=None, margins=(0, 0, 0, 0)):
        self._rows = []
        self._named_rows = {}
        self._spacing = spacing
        self._column_spacing = column_spacing if column_spacing is not None else spacing
        self._margins = margins

    def add(self, widget, *, name=None, stretch=0, scrollable=False):
        """Add a single widget as a row"""
        self._rows.append((widget, stretch, scrollable))
        if name:
            self._named_rows[name] = widget
        return self

    def addHorizontal(self, widgets, *, stretches=None,
                      name=None, stretch=0, scrollable=False):
        """Pack widgets side by side"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._column_spacing)
        if stretches is None:
            stretches = [1] * len(widgets)
        for w, s in zip(widgets, stretches):
            layout.addWidget(w, s)
        self._rows.append((container, stretch, scrollable))
        if name:
            self._named_rows[name] = container
        return self

    def addColumns(self, widgets, *, max_columns=5, compact_threshold=5,
                   name=None, stretch=1, scrollable=True):
        """Add a dynamic column grid row"""
        if len(widgets) <= compact_threshold:
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(self._column_spacing)
            for w in widgets:
                layout.addWidget(w)
            layout.addStretch(1)
            row = container
        else:
            row = ColumnsRow(widgets, max_columns=max_columns, spacing=self._column_spacing)
        self._rows.append((row, stretch, scrollable))
        if name:
            self._named_rows[name] = row
        return self

    def row(self, name):
        """Retrieve a named row widget"""
        return self._named_rows.get(name)

    def build(self):
        """Create and return top-level container"""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(*self._margins)
        main_layout.setSpacing(self._spacing)
        for widget, stretch, scrollable in self._rows:
            if scrollable:
                scroll = QScrollArea()
                scroll.setWidget(widget)
                scroll.setWidgetResizable(True)
                scroll.setFrameShape(QScrollArea.NoFrame)
                main_layout.addWidget(scroll, stretch)
            else:
                main_layout.addWidget(widget, stretch)
        return container
