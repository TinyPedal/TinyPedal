"""Filter effect — dims non-matching rows across tables and order lists"""
class FilterEffect:

    def __init__(self):
        self._tables = []
        self._order_lists = []

    def add_table(self, table):
        self._tables.append(table)

    def add_order_list(self, order_list):
        self._order_lists.append(order_list)

    def apply(self, text):
        text = text.strip().lower()
        for table in self._tables:
            self._filter_table(table, text)
        for order_list in self._order_lists:
            order_list.apply_filter(text)

    def _filter_table(self, table, text):
        title_dimded = (
            "background-color: palette(mid);"
            "color: palette(window);"
            "border-bottom: 2px solid palette(mid);"
            "padding: 4px;"
        )

        if not text:
            for key in table.keys():
                self._undim_row(table, key)
            if table.title_label is not None:
                table.title_label.setStyleSheet("")
            return
        all_dimmed = True
        for key in table.keys():
            if text in key.lower():
                self._undim_row(table, key)
                all_dimmed = False
            else:
                self._dim_row(table, key)
        if table.title_label is not None:
            table.title_label.setStyleSheet(
                title_dimded if all_dimmed else "")

    @staticmethod
    def _dim_row(table, key):
        row = table.row_widget(key)
        if row is None:
            return
        row.setStyleSheet("background-color: palette(window);")
        label = table.row_label(key)
        if label is not None:
            label.setStyleSheet("color: palette(mid);")

    @staticmethod
    def _undim_row(table, key):
        row = table.row_widget(key)
        if row is None:
            return
        bg = row.property("_base_bg") or "palette(base)"
        row.setStyleSheet(f"background-color: {bg};")
        label = table.row_label(key)
        if label is not None:
            label.setStyleSheet("")
