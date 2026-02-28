from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget


class ColumnsZone(QWidget):
    """
    Places widgets in a dynamic column grid.
    Number of columns adapts to available width, up to max_columns.
    """

    def __init__(self, widgets, max_columns=5, parent=None):
        super().__init__(parent)
        self._widgets = widgets[:]
        self.max_columns = max_columns
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(1)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._reflow)

        self._reflow()

    @property
    def widgets(self):
        return self._widgets

    @widgets.setter
    def widgets(self, new_widgets):
        self._widgets = new_widgets[:]
        self._reflow()

    def _reflow(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                try:
                    widget.setParent(None)
                except RuntimeError:
                    pass

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
            avail_width = self.parent().width() if self.parent() else 800

        widest = 1
        still_alive = []
        for w in self._widgets:
            try:
                hint = w.sizeHint().width()
                if hint > widest:
                    widest = hint
                still_alive.append(w)
            except RuntimeError:
                continue
        self._widgets = still_alive

        if not self._widgets:
            self.updateGeometry()
            return

        num_cols = max(1, min(self.max_columns, avail_width // max(widest, 1)))

        for idx, w in enumerate(self._widgets):
            try:
                self.grid.addWidget(w, idx // num_cols, idx % num_cols)
                w.show()
            except RuntimeError:
                continue

        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(50)


class LayoutBuilder:
    """
    Builds a vertical stack of zones with per-zone scroll support.

    Usage:
        builder = LayoutBuilder(spacing=2, margins=(4, 4, 4, 4))
        builder.add_zone(preview, name='preview')
        builder.add_horizontal_zone([general, sections], name='info')
        builder.add_zone(search, name='search')
        builder.add_columns_zone(tables, max_columns=5, scrollable=True, name='content')
        widget = builder.build()
    """

    def __init__(self, spacing=2, margins=(0, 0, 0, 0)):
        self.zones = []
        self.named_zones = {}
        self._spacing = spacing
        self._margins = margins

    def add_zone(self, widget, name=None, stretch=0, scrollable=False):
        """Add a single widget as a zone."""
        self.zones.append((widget, stretch, scrollable))
        if name:
            self.named_zones[name] = widget

    def add_horizontal_zone(self, widgets, name=None, stretch=0, scrollable=False):
        """Add multiple widgets side by side as a zone."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        for w in widgets:
            layout.addWidget(w)
        layout.addStretch(1)
        self.zones.append((container, stretch, scrollable))
        if name:
            self.named_zones[name] = container

    def add_columns_zone(self, widgets, max_columns=5, compact_threshold=5,
                         name=None, stretch=1, scrollable=True):
        """Add widgets in a dynamic column grid, or vertical stack if compact."""
        if len(widgets) <= compact_threshold:
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            for w in widgets:
                layout.addWidget(w)
            layout.addStretch(1)
            zone = container
        else:
            zone = ColumnsZone(widgets, max_columns)

        self.zones.append((zone, stretch, scrollable))
        if name:
            self.named_zones[name] = zone

    def build(self):
        """
        Build and return a QWidget containing all zones.
        Scrollable zones are wrapped in a QScrollArea.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(*self._margins)
        layout.setSpacing(self._spacing)

        for zone, stretch, scrollable in self.zones:
            if scrollable:
                scroll = QScrollArea()
                scroll.setWidget(zone)
                scroll.setWidgetResizable(True)
                scroll.setFrameShape(QScrollArea.NoFrame)
                layout.addWidget(scroll, stretch)
            else:
                layout.addWidget(zone, stretch)

        return container
