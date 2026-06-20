#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2026 TinyPedal developers, see contributors.md file
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
Notes module
"""

from __future__ import annotations

from typing import Callable, Mapping

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_file import FileExt
from ..module_info import NotesInfo, minfo
from ..userfile.track_notes import (
    COLUMN_DISTANCE,
    COLUMN_TAGS,
    HEADER_PACE_NOTES,
    HEADER_TRACK_NOTES,
    TAG_PITNOTES,
    load_notes_file,
    parse_csv_notes_only,
)
from ..validator import generator_init
from ._base import DataModule


class Realtime(DataModule):
    """Notes data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        userpath_pace_notes = self.cfg.path.pace_notes
        userpath_track_notes = self.cfg.path.track_notes
        output_pacenotes = minfo.pacenotes
        output_tracknotes = minfo.tracknotes
        output_pacenotes_pit = minfo.pacenotes_pit
        output_tracknotes_pit = minfo.tracknotes_pit

        setting_playback = self.cfg.user.setting["pace_notes_playback"]

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    track_name = api.read.session.track_name()

                    # Load pace notes
                    pace_notes = load_pace_notes_file(
                        config=setting_playback,
                        filepath=userpath_pace_notes,
                        filename=track_name,
                        table_header=HEADER_PACE_NOTES,
                        parser=parse_csv_notes_only,
                        extension=FileExt.TPPN,
                    )
                    if pace_notes:
                        gen_pacenotes = notes_selector(
                            output=output_pacenotes,
                            dataset=filter_notes(pace_notes),
                            pit_only=False,
                        )
                        gen_pacenotes_pit = notes_selector(
                            output=output_pacenotes_pit,
                            dataset=filter_tags(pace_notes, TAG_PITNOTES),
                            pit_only=True,
                        )

                    # Load track notes
                    track_notes = load_notes_file(
                        filepath=userpath_track_notes,
                        filename=track_name,
                        table_header=HEADER_TRACK_NOTES,
                        parser=parse_csv_notes_only,
                        extension=FileExt.TPTN,
                    )
                    if track_notes:
                        gen_tracknotes = notes_selector(
                            output=output_tracknotes,
                            dataset=filter_notes(track_notes),
                            pit_only=False,
                        )
                        gen_tracknotes_pit = notes_selector(
                            output=output_tracknotes_pit,
                            dataset=filter_tags(track_notes, TAG_PITNOTES),
                            pit_only=True,
                        )

                # Update position
                pos_synced = minfo.delta.lapDistance

                # Update pace notes
                if pace_notes:
                    pos_offset = pos_synced + setting_playback["pace_notes_global_offset"]
                    gen_pacenotes.send(pos_offset)
                    gen_pacenotes_pit.send(pos_offset)

                # Update track notes
                if track_notes:
                    gen_tracknotes.send(pos_synced)
                    gen_tracknotes_pit.send(pos_synced)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    output_pacenotes.reset()
                    output_tracknotes.reset()
                    output_pacenotes_pit.reset()
                    output_tracknotes_pit.reset()


def load_pace_notes_file(
    config: dict, filepath: str, filename: str,
    table_header: tuple, parser: Callable, extension: str):
    """Load pace notes"""
    if config["enable_manual_file_selector"]:
        filepath = ""
        filename = config["pace_notes_file_name"]
        extension = ""
    return load_notes_file(
        filepath=filepath,
        filename=filename,
        table_header=table_header,
        parser=parser,
        extension=extension,
    )


@generator_init
def notes_selector(output: NotesInfo, dataset: tuple[Mapping, ...], pit_only: bool):
    """Notes selector

    Args:
        output: module info.
        dataset: list of notes.
    """
    last_index = -99999  # make sure initial index is different
    next_index = 0  # next note line index
    pos_reference = reference_position(dataset)
    end_index = len(pos_reference) - 1  # end note line index
    pos_final = pos_reference[-1] if pos_reference else 0.0  # final reference position
    output.reset()  # initial reset before updating

    while True:
        pos_curr = yield

        if not pos_reference:
            continue

        curr_index = calc.binary_search_lower(pos_reference, pos_curr, 0, end_index)

        if last_index == curr_index:
            continue

        last_index = curr_index
        next_index = (curr_index + 1) * (pos_curr < pos_final)

        if curr_index < 0:
            curr_index = end_index

        output.currentIndex = curr_index
        output.currentNote = dataset[curr_index]
        output.nextIndex = next_index
        output.nextNote = dataset[next_index]


def filter_notes(dataset: list[Mapping]) -> tuple[Mapping, ...]:
    """Filter notes without tags"""
    return tuple(_note for _note in dataset if not _note.get(COLUMN_TAGS))


def filter_tags(dataset: list[Mapping], tag_name: str) -> tuple[Mapping, ...]:
    """Filter notes with specific tag"""
    return tuple(_note for _note in dataset if tag_name in _note.get(COLUMN_TAGS, ""))


def reference_position(notes: list[Mapping]) -> tuple[float, ...]:
    """Reference notes position list"""
    return tuple(note_line[COLUMN_DISTANCE] for note_line in notes)
