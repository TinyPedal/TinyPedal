"""Highlight effect — highlights rows by key across tables"""
class HighlightEffect:

    def __init__(self):
        self._tables = []
        self._active_keys = set()

    def add_table(self, table):
        self._tables.append(table)

    def apply(self, keys):
        self.clear()
        self._active_keys = set(keys)
        for table in self._tables:
            for key in self._active_keys:
                row = table.row_widget(key)
                if row:
                    row.setStyleSheet("background-color: lightblue;")

    def clear(self):
        if not self._active_keys:
            return
        for table in self._tables:
            for key in self._active_keys:
                row = table.row_widget(key)
                if row:
                    bg = row.property("_base_bg") or "palette(base)"
                    row.setStyleSheet(f"background-color: {bg};")
        self._active_keys.clear()
