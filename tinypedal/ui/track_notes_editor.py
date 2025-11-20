#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Track & pace notes editor
"""

import os

from PySide2.QtCore import QPoint, Qt
from PySide2.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..api_control import api
from ..formatter import strip_invalid_char
from ..setting import cfg
from ..userfile.track_notes import (
    NOTESTYPE_PACE,
    NOTESTYPE_TRACK,
    create_notes_metadata,
    load_notes_file,
    save_notes_file,
    set_notes_filter,
    set_notes_header,
    set_notes_parser,
    set_notes_writer,
)
from ._common import (
    QVAL_FILENAME,
    BaseDialog,
    BaseEditor,
    BatchOffset,
    CompactButton,
    FloatTableItem,
    TableBatchReplace,
    UIScaler,
)
from .track_map_viewer import MapView

DECIMALS = 2


def set_file_path(notes_type: str, filename: str = "") -> str:
    """Set file path"""
    if notes_type == NOTESTYPE_PACE:
        filepath = cfg.path.pace_notes
    else:
        filepath = cfg.path.track_notes
    return f"{filepath}{filename}"


class TrackNotesEditor(BaseEditor):
    """Track & pace notes editor"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Track Notes Editor")

        self.notes_type = None
        self.notes_header = None
        self.notes_metadata = create_notes_metadata()
        self.notes_temp = []
        self._verify_enabled = True

        # Set status bar
        self.status_bar = QStatusBar(self)

        # Set panels
        self.trackmap_panel = self.set_layout_trackmap()
        self.editor_panel = self.set_layout_editor()
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(5)
        splitter.addWidget(self.trackmap_panel)
        splitter.addWidget(self.editor_panel)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0,1)

        # Init setting & table
        self.create_pacenotes()

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, 0)
        layout_main.addWidget(splitter, stretch=1)
        layout_main.addWidget(self.status_bar)
        self.setLayout(layout_main)

    def toggle_trackmap_panel(self):
        """Toggle trackmap panel"""
        if self.trackmap_panel.isHidden():
            self.trackmap_panel.show()
            self.button_showmap.setText("Hide Map")
        else:
            self.trackmap_panel.hide()
            self.button_showmap.setText("Show Map")

    def set_layout_trackmap(self):
        """Set track map panel"""
        self.trackmap = MapView(self)
        self.trackmap.reloaded.connect(self.mark_positions_on_map)

        layout_map_wrap = QVBoxLayout()
        layout_map_wrap.addWidget(self.trackmap)
        layout_map_wrap.setContentsMargins(0, 0, 0, 0)

        frame_trackmap = QFrame(self)
        frame_trackmap.setLayout(layout_map_wrap)
        frame_trackmap.setFrameShape(QFrame.StyledPanel)

        layout_trackmap = QVBoxLayout()
        layout_trackmap.addLayout(self.trackmap.set_button_layout())
        layout_trackmap.addWidget(frame_trackmap)
        layout_trackmap.addLayout(self.trackmap.set_control_layout())
        layout_trackmap.setContentsMargins(0, 0, 0, 0)

        trackmap_panel = QFrame(self)
        trackmap_panel.setMinimumSize(UIScaler.size(38), UIScaler.size(38))
        trackmap_panel.setLayout(layout_trackmap)
        return trackmap_panel

    def set_layout_editor(self):
        """Set editor panel"""
        # Notes table
        self.table_notes = QTableWidget(self)
        self.table_notes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_notes.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_notes.cellChanged.connect(self.verify_input)

        self.table_context_menu = self.set_context_menu()
        self.table_notes.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_notes.customContextMenuRequested.connect(self.open_context_menu)

        # Notes filename edit
        self.filename_entry = QLineEdit()
        self.filename_entry.setValidator(QVAL_FILENAME)

        # File menu
        file_menu = QMenu(self)

        open_pacenotes = file_menu.addAction("Open Pace Notes")
        open_pacenotes.triggered.connect(self.load_pacenotes_file)

        open_tracknotes = file_menu.addAction("Open Track Notes")
        open_tracknotes.triggered.connect(self.load_tracknotes_file)
        file_menu.addSeparator()

        create_pacenotes = file_menu.addAction("New Pace Notes")
        create_pacenotes.triggered.connect(self.create_pacenotes)

        create_tracknotes = file_menu.addAction("New Track Notes")
        create_tracknotes.triggered.connect(self.create_tracknotes)

        button_file = CompactButton("File", has_menu=True)
        button_file.setMenu(file_menu)

        # Set position menu
        setpos_menu = QMenu(self)

        setpos_frommap = setpos_menu.addAction("From Map")
        setpos_frommap.triggered.connect(self.set_position_from_map)

        setpos_fromtele = setpos_menu.addAction("From Telemetry")
        setpos_fromtele.triggered.connect(self.set_position_from_tele)

        button_setpos = CompactButton("Set Pos", has_menu=True)
        button_setpos.setMenu(setpos_menu)

        # Button
        self.button_showmap = CompactButton("Hide Map")
        self.button_showmap.clicked.connect(self.toggle_trackmap_panel)

        button_add = CompactButton("Add")
        button_add.clicked.connect(self.add_notes)

        button_insert = CompactButton("Insert")
        button_insert.clicked.connect(self.insert_notes)

        button_sort = CompactButton("Sort")
        button_sort.clicked.connect(self.sort_notes)

        button_delete = CompactButton("Delete")
        button_delete.clicked.connect(self.delete_notes)

        button_replace = CompactButton("Replace")
        button_replace.clicked.connect(self.open_replace_dialog)

        button_offset = CompactButton("Offset")
        button_offset.clicked.connect(self.open_offset_dialog)

        button_metadata = CompactButton("Info")
        button_metadata.clicked.connect(self.open_metadata_dialog)

        button_save = CompactButton("Save")
        button_save.clicked.connect(self.saving)

        button_close = CompactButton("Close")
        button_close.clicked.connect(self.close)

        layout_top = QHBoxLayout()
        layout_top.addWidget(self.button_showmap)
        layout_top.addWidget(button_file)
        layout_top.addWidget(self.filename_entry, stretch=1)
        layout_top.addWidget(button_metadata)
        layout_top.addWidget(button_save)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_setpos)
        layout_button.addWidget(button_add)
        layout_button.addWidget(button_insert)
        layout_button.addWidget(button_sort)
        layout_button.addWidget(button_delete)
        layout_button.addWidget(button_replace)
        layout_button.addWidget(button_offset)
        layout_button.addStretch(1)
        layout_button.addWidget(button_close)

        layout_editor = QVBoxLayout()
        layout_editor.addLayout(layout_top)
        layout_editor.addWidget(self.table_notes)
        layout_editor.addLayout(layout_button)
        layout_editor.setContentsMargins(0, 0, 0, 0)

        editor_panel = QFrame(self)
        editor_panel.setMinimumSize(UIScaler.size(38), UIScaler.size(38))
        editor_panel.setLayout(layout_editor)
        return editor_panel

    def set_notes_type(self, notes_type: str):
        """Set notes type"""
        self.notes_type = notes_type
        self.notes_header = set_notes_header(notes_type)
        self.status_bar.showMessage(f"Edit Mode: {notes_type}", 0)
        self.filename_entry.setPlaceholderText(f"{notes_type} Name")

    def create_pacenotes(self):
        """Create pace notes file"""
        self.create_new_file(NOTESTYPE_PACE)

    def create_tracknotes(self):
        """Load track notes file"""
        self.create_new_file(NOTESTYPE_TRACK)

    def create_new_file(self, notes_type: str):
        """Create new file"""
        if not self.confirm_discard():
            return

        self.set_notes_type(notes_type)
        self.filename_entry.setText(self.get_track_name())
        self.notes_temp.clear()
        self.notes_metadata.update(create_notes_metadata())
        self.refresh_table()
        self.add_notes()
        self.set_unmodified()

    def load_pacenotes_file(self):
        """Load pace notes file"""
        self.load_from_file(NOTESTYPE_PACE)

    def load_tracknotes_file(self):
        """Load track notes file"""
        self.load_from_file(NOTESTYPE_TRACK)

    def load_from_file(self, notes_type: str):
        """Load notes from file"""
        if not self.confirm_discard():
            return

        filename_full, file_filter = QFileDialog.getOpenFileName(
            self,
            dir=set_file_path(notes_type),
            filter=set_notes_filter(notes_type),
        )
        if not filename_full:
            return

        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.basename(filename_full)
        notes_header = set_notes_header(notes_type)
        notes_parsed = load_notes_file(
            filepath=filepath,
            filename=filename,
            table_header=notes_header,
            parser=set_notes_parser(file_filter),
        )

        if notes_parsed is None:
            msg_text = "Cannot open selected file.<br><br>Invalid notes file."
            QMessageBox.warning(self, "Error", msg_text)
            return

        notes_sorted, meta_info = notes_parsed
        self.set_notes_type(notes_type)
        self.notes_temp = notes_sorted
        self.notes_metadata.update(meta_info)
        self.filename_entry.setText(filename)
        self.refresh_table()
        self.set_unmodified()
        self.mark_positions_on_map()

    def refresh_table(self):
        """Refresh notes table"""
        self.table_notes.setRowCount(0)
        self.table_notes.setColumnCount(len(self.notes_header))
        self.table_notes.setHorizontalHeaderLabels(self.notes_header)
        self.table_notes.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_notes.setColumnWidth(0, UIScaler.size(6))

        self._verify_enabled = False
        for row_index, note_line in enumerate(self.notes_temp):
            self.table_notes.insertRow(row_index)
            for column_index, fieldname in enumerate(self.notes_header):
                value = note_line[fieldname]
                if column_index == 0:
                    item = FloatTableItem(round(value, DECIMALS))
                else:
                    item = QTableWidgetItem(value)
                self.table_notes.setItem(row_index, column_index, item)
        self._verify_enabled = True

    def open_replace_dialog(self):
        """Open replace dialog"""
        selector = {name:idx for idx, name in enumerate(self.notes_header) if idx > 0}
        _dialog = TableBatchReplace(self, selector, self.table_notes)
        _dialog.open()

    def open_metadata_dialog(self):
        """Open metadata dialog"""
        _dialog = MetaDataEditor(self, self.notes_metadata)
        _dialog.open()

    def open_offset_dialog(self):
        """Open offset dialog"""
        if self.column_selection_count(0) == 0:
            msg_text = (
                "Select <b>one or more values</b> from <b>distance</b> "
                "column to apply offset."
            )
            QMessageBox.warning(self, "Error", msg_text)
            return

        _dialog = BatchOffset(self, self.apply_batch_offset)
        _dialog.config(2, 0.1, -99999, 99999)
        _dialog.open()

    def apply_batch_offset(self, offset: float, is_scale_mode: bool):
        """Apply batch offset"""
        self._verify_enabled = False
        for item in self.table_notes.selectedItems():
            value = item.value()
            if is_scale_mode:
                value *= offset
            else:
                value += offset
            item.setValue(round(value, DECIMALS))
        self._verify_enabled = True
        self.set_modified()
        self.mark_positions_on_map()

    def set_position_from_map(self):
        """Set position from map"""
        self.set_position(float(self.trackmap.map_seek_dist), "from map")

    def set_position_from_tele(self):
        """Set position from telemetry"""
        self.set_position(api.read.lap.distance(), "from telemetry")

    def set_position(self, position: float, source: str):
        """Set position to selected cell"""
        if self.column_selection_count(0) != 1:  # limit to one selected cell
            msg_text = (
                "Select <b>one value</b> from <b>distance</b> column to set position."
            )
            QMessageBox.warning(self, "Error", msg_text)
            return

        if not self.confirm_operation(message=f"Set position at <b>{position}</b> {source}?"):
            return

        pos_curr = round(position, DECIMALS)
        row_index = self.table_notes.currentRow()
        self.table_notes.item(row_index, 0).setValue(pos_curr)
        self.mark_positions_on_map()
        self.highlight_position_on_map()
        self.table_notes.setCurrentCell(-1, -1)  # deselect to avoid mis-clicking

    def add_notes(self):
        """Add new notes entry"""
        self.add_table_row(
            self.table_notes.rowCount(),
            self.table_notes.columnCount()
        )

    def insert_notes(self, row_offset: int = 0):
        """Insert new notes entry"""
        self.add_table_row(
            self.table_notes.currentRow() + row_offset,
            self.table_notes.columnCount()
        )

    def sort_notes(self) -> bool:
        """Sort notes by distance in ascending order"""
        if self.table_notes.rowCount() > 1:
            self.table_notes.sortItems(0)
            self.set_modified()
        return True

    def delete_notes(self):
        """Delete notes entry"""
        selected_rows = set(data.row() for data in self.table_notes.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Error", "No data selected.")
            return

        if not self.confirm_operation(message="<b>Delete selected rows?</b>"):
            return

        for row_index in sorted(selected_rows, reverse=True):
            self.table_notes.removeRow(row_index)
        self.set_modified()
        self.mark_positions_on_map()

    def update_notes_temp(self, table_header):
        """Update temporary changes to notes temp"""
        temp = (
            {
                fieldname: self.parse_notes(
                    self.table_notes.item(row_index, column_index), column_index
                )
                for column_index, fieldname in enumerate(table_header)
            }
            for row_index in range(self.table_notes.rowCount())
        )
        self.notes_temp = list(temp)

    @staticmethod
    def parse_notes(item, index: int):
        """Parse notes"""
        if index == 0:
            return round(item.value(), DECIMALS)
        return item.text()

    def saving(self):
        """Save notes"""
        self.save_notes(self.notes_type)

    def save_notes(self, notes_type: str):
        """Save notes"""
        if not self.sort_notes():
            return

        self.update_notes_temp(self.notes_header)

        if not self.notes_temp:
            QMessageBox.warning(self, "Error", "Nothing to save.")
            return

        filename = self.filename_entry.text()
        if not filename:  # try find track name if file name was not set
            filename = self.get_track_name()

        filename_full, file_filter = QFileDialog.getSaveFileName(
            self,
            dir=set_file_path(notes_type, filename),
            filter=set_notes_filter(notes_type),
        )
        if not filename_full:  # save canceled
            return

        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.basename(filename_full)
        save_notes_file(
            filepath=filepath,
            filename=filename,
            table_header=self.notes_header,
            dataset=self.notes_temp,
            metadata=self.notes_metadata,
            writer=set_notes_writer(file_filter),
        )
        self.filename_entry.setText(filename)
        self.set_unmodified()
        msg_text = f"Notes saved at:<br><b>{filename_full}</b>"
        QMessageBox.information(self, "Saved", msg_text)

    def column_selection_count(self, column_index: int = 0) -> int:
        """Column selection count"""
        row_count = 0
        for data in self.table_notes.selectedIndexes():
            if data.column() == column_index:
                row_count += 1
            else:
                return 0
        return row_count

    def verify_input(self, row_index: int, column_index: int):
        """Verify input value"""
        if self._verify_enabled:
            self.set_modified()
            item = self.table_notes.item(row_index, column_index)
            if column_index == 0:
                item.validate()
                self.mark_positions_on_map()
            elif column_index == 1 and self.notes_type == NOTESTYPE_PACE:
                # Remove invalid char (filename) from pace note column
                item.setText(strip_invalid_char(item.text()))

    def set_context_menu(self):
        """Set context menu"""
        menu = QMenu(self)
        menu.addAction("Highlight on Map")
        menu.addSeparator()
        menu.addAction("Set from Map")
        menu.addAction("Set from Telemetry")
        menu.addSeparator()
        menu.addAction("Insert Row Above")
        menu.addAction("Insert Row Below")
        menu.addAction("Delete Rows")
        return menu

    def open_context_menu(self, position: QPoint):
        """Open context menu"""
        if not self.table_notes.itemAt(position):
            return

        position += QPoint(  # position correction from header
            self.table_notes.verticalHeader().width(),
            self.table_notes.horizontalHeader().height(),
        )
        selected_action = self.table_context_menu.exec_(
            self.table_notes.mapToGlobal(position))
        if not selected_action:
            return

        action = selected_action.text()
        if action == "Highlight on Map":
            self.mark_positions_on_map()
            self.highlight_position_on_map()
        elif action == "Set from Map":
            self.set_position_from_map()
        elif action == "Set from Telemetry":
            self.set_position_from_tele()
        elif action == "Insert Row Above":
            self.insert_notes(0)
        elif action == "Insert Row Below":
            self.insert_notes(1)
        elif action == "Delete Rows":
            self.delete_notes()

    def highlight_position_on_map(self):
        """Highlight selected position on map"""
        value = self.table_notes.item(self.table_notes.currentRow(), 0).value()
        self.trackmap.spinbox_pos_dist.setValue(value)
        self.trackmap.update_highlighted_coords()

    def mark_positions_on_map(self):
        """Mark all positions on map"""
        temp_coords = set(
            self.table_notes.item(row_index, 0).value()
            for row_index in range(self.table_notes.rowCount())
        )
        self.trackmap.update_marked_coords(temp_coords)

    def get_track_name(self) -> str:
        """Get track name"""
        track_name = api.read.session.track_name()
        if not track_name:
            return self.trackmap.map_filename
        return track_name

    def add_table_row(self, row_index: int, column_count: int):
        """Add new table row"""
        self.table_notes.insertRow(row_index)
        self.table_notes.setCurrentCell(row_index, 0)
        for column_index in range(column_count):
            if column_index == 0:
                item = FloatTableItem(0)
            else:
                item = QTableWidgetItem("")
            self.table_notes.setItem(row_index, column_index, item)


class MetaDataEditor(BaseDialog):
    """Metadata editor"""

    def __init__(self, parent, metadata: dict):
        super().__init__(parent)
        self.setWindowTitle("Metadata Info")

        self.metadata = metadata
        self.option_metadata = {}

        # Label & Edit
        layout_option = QGridLayout()
        layout_option.setAlignment(Qt.AlignTop)

        for idx, fieldname in enumerate(metadata):
            desc_label = QLabel(f"{fieldname.capitalize()}:")
            edit_entry = QLineEdit()
            edit_entry.setText(metadata[fieldname])
            layout_option.addWidget(desc_label, idx, 0)
            layout_option.addWidget(edit_entry, idx, 1)
            self.option_metadata[fieldname] = edit_entry

        # Button
        button_save = QPushButton("Ok")
        button_save.clicked.connect(self.saving)

        button_close = QPushButton("Close")
        button_close.clicked.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.addStretch(1)
        layout_button.addWidget(button_save)
        layout_button.addWidget(button_close)

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_option)
        layout_main.addLayout(layout_button)
        self.setLayout(layout_main)
        self.setMinimumWidth(UIScaler.size(38))
        self.setFixedHeight(self.sizeHint().height())

    def saving(self):
        """Save metadata"""
        self.metadata.update({key:edit.text() for key, edit in self.option_metadata.items()})
        self.accept()
