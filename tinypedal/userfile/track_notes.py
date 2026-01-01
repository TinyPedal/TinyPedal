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
Track & pace notes file function
"""

from __future__ import annotations

import csv
import logging
import os
from operator import itemgetter
from typing import Any, Callable, Iterable

from ..const_common import CRLF
from ..const_file import FileFilter

NOTESTYPE_PACE = "Pace Notes"
NOTESTYPE_TRACK = "Track Notes"

COLUMN_DISTANCE = "distance"
COLUMN_PACENOTE = "pace note"
COLUMN_TRACKNOTE = "track note"
COLUMN_COMMENT = "comment"

HEADER_PACE_NOTES = COLUMN_DISTANCE, COLUMN_PACENOTE, COLUMN_COMMENT
HEADER_TRACK_NOTES = COLUMN_DISTANCE, COLUMN_TRACKNOTE, COLUMN_COMMENT

METADATA_FIELDNAMES = "TITLE", "AUTHOR", "DATE", "DESCRIPTION"

logger = logging.getLogger(__name__)


def set_notes_filter(notes_type: str) -> str:
    """Set notes file filter"""
    if notes_type == NOTESTYPE_PACE:
        filter_set = (  # pace notes filters
            FileFilter.TPPN,
            FileFilter.GPLINI,
            FileFilter.CSV,
            FileFilter.INI,
            FileFilter.ALL,
        )
    else:
        filter_set = (  # track notes filters
            FileFilter.TPTN,
            FileFilter.CSV,
            FileFilter.INI,
            FileFilter.ALL,
        )
    return ";;".join(filter_set)


def set_notes_header(notes_type: str) -> tuple[str, ...]:
    """Set notes header"""
    if notes_type == NOTESTYPE_PACE:
        return HEADER_PACE_NOTES
    return HEADER_TRACK_NOTES


def set_notes_parser(file_filter: str) -> Callable:
    """Set notes parser"""
    if file_filter == FileFilter.GPLINI:
        return parse_gpl_notes
    return parse_csv_notes


def set_notes_writer(file_filter: str) -> Callable:
    """Set notes writer"""
    if file_filter == FileFilter.GPLINI:
        return write_gpl_notes
    return write_csv_notes


def create_notes_metadata() -> dict:
    """Create notes metadata"""
    return {key: "" for key in METADATA_FIELDNAMES}


def parse_csv_notes(notes_file: Iterable[str], table_header: tuple[str, ...]):
    """Parse TinyPedal notes"""
    notes_reader = csv.DictReader(
        notes_file, fieldnames=table_header, restval="", restkey="unknown")
    column_key = table_header[0]
    column_value = table_header[1]
    metadata_checked = False
    meta_info = create_notes_metadata()
    notes_temp = []
    for note_line in notes_reader:
        # Load metadata
        if not metadata_checked:
            key = note_line[column_key]
            if key in meta_info:
                meta_info[key] = note_line[column_value]
                continue
            if key == column_key:  # found start of header, set checked
                metadata_checked = True
                continue
        # Load notes
        if verify_notes(note_line, column_key):
            if not metadata_checked:  # found first valid number, set checked
                metadata_checked = True
            notes_temp.append(note_line)
    return sorted(notes_temp, key=itemgetter(column_key)), meta_info


def parse_gpl_notes(notes_file: Iterable[str], table_header: tuple[str, ...]):
    """Parse GPL pace notes"""
    meta_info = create_notes_metadata()
    meta_info_keys = meta_info.keys()
    column_key = table_header[0]
    metadata_checked = False
    notes_temp = []
    for note_line in notes_file:
        # Skip comments and empty lines
        if note_line.startswith(";") or ".mp3" not in note_line:
            # Load metadata
            if not metadata_checked:
                for meta_key in meta_info_keys:
                    if meta_key in note_line:
                        meta_info[meta_key] = note_line.lstrip(f";{meta_key}:").strip()
                        continue
            continue
        # Parse notes
        split_line = note_line.rstrip().split(",", 1)
        pace_note = split_line[0].strip()[:-4]  # strip extension
        if len(split_line) > 1:
            if not metadata_checked:  # found first valid number, set checked
                metadata_checked = True
            split_string = split_line[-1].split(";", 1)
            distance = float(split_string[0].strip())
            if len(split_string) > 1:
                annotation = split_string[1].strip()
            else:
                annotation = ""
            notes_temp.append(
                {
                    table_header[0]: distance,
                    table_header[1]: pace_note,
                    table_header[2]: annotation,
                }
            )
    return sorted(notes_temp, key=itemgetter(column_key)), meta_info


def parse_csv_notes_only(notes_file: Iterable[str], table_header: tuple[str, ...]):
    """Parse TinyPedal notes without metadata"""
    column_key = table_header[0]
    notes_read = csv.DictReader(
        notes_file, fieldnames=table_header, restval="", restkey="unknown")
    lastlist = (note_line for note_line in notes_read if verify_notes(note_line, column_key))
    return sorted(lastlist, key=itemgetter(column_key))


def load_notes_file(
    filepath: str, filename: str, table_header: tuple[str, ...],
    parser: Callable = parse_csv_notes, extension: str = ""):
    """Load notes file"""
    try:
        filename_full = f"{filepath}{filename}{extension}"
        if os.path.getsize(filename_full) > 1024000:  # limit file size under 1024kb
            raise TypeError

        with open(filename_full, newline="", encoding="utf-8") as temp_file:
            return parser(temp_file, table_header)

    except FileNotFoundError:
        logger.info("MISSING: track notes (%s) data", extension)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, OSError):
        logger.info("MISSING: invalid track notes (%s) data", extension)
    return None


def write_csv_notes(
    notes_file: Any, table_header: tuple, dataset: list, metadata: dict, _: str):
    """Write TinyPedal notes format to file"""
    # Write TinyPedal file version
    notes_file.write(f"TINYPEDAL {table_header[1].upper()}S FILE VERSION,1")
    notes_file.write(CRLF * 2)
    # Write metadata
    meta_output = CRLF.join(f"{key},\"{value}\"" for key, value in metadata.items())
    notes_file.write(meta_output)
    notes_file.write(CRLF * 2)
    # Write notes
    notes_writer = csv.DictWriter(
        notes_file, fieldnames=table_header, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL
    )
    notes_writer.writeheader()
    notes_writer.writerows(dataset)


def write_gpl_notes(
    notes_file: Any, table_header: tuple, dataset: list, metadata: dict, filename: str):
    """Write GPL pace notes format to file

    Pace notes formatting follows GPL pace notes 'Version 3' specification by Lee Bowden.
    """
    # Write metadata
    meta_output = CRLF.join(f";{key}: {value}" for key, value in metadata.items())
    line_separator = f";{'*' * 27}{CRLF}"
    notes_file.write(line_separator)
    notes_file.write(f";GPL PACE NOTES .INI FILE  Version 3{CRLF}")
    notes_file.write(f";{filename[:-4]}{CRLF}")
    notes_file.write(line_separator)
    notes_file.write(CRLF)
    notes_file.write(meta_output)
    notes_file.write(CRLF * 2)
    notes_file.write(line_separator)
    notes_file.write(CRLF)
    notes_file.write(f";Any line beginning with a ; is a comment and is ignored{CRLF}")
    notes_file.write(f";Any information to the right of a ; is a comment and is ignored{CRLF}")
    notes_file.write(f";Any line beginning with a space is ignored{CRLF}")
    notes_file.write(CRLF)
    notes_file.write(line_separator)
    notes_file.write(CRLF)
    notes_file.write(f";This section contains the sound entries with:{CRLF}")
    notes_file.write(f";1) Sound filename including the .mp3 suffix{CRLF}")
    notes_file.write(f";2) Distance in meters from the track start point to play the sound{CRLF}")
    notes_file.write(CRLF)
    notes_file.write(line_separator)
    notes_file.write(CRLF)
    # Write notes
    for note_line in dataset:
        notes_file.write(
            f"{note_line[table_header[1]]}.mp3, "  # sound file name
            f"{note_line[table_header[0]]:.0f}; "  # distance integer
            f"{note_line[table_header[2]]}{CRLF}"  # comment
        )
    notes_file.write(CRLF)


def save_notes_file(
    filepath: str, filename: str, table_header: tuple, dataset: list, metadata: dict,
    writer: Callable = write_csv_notes, extension: str = ""
) -> None:
    """Save notes file"""
    if len(dataset) < 1:
        return
    with open(f"{filepath}{filename}{extension}", "w", newline="", encoding="utf-8") as temp_file:
        writer(temp_file, table_header, dataset, metadata, filename)


def verify_notes(note_line: dict, column_key: str) -> bool:
    """Verify notes and show errors"""
    try:
        note_line[column_key] = float(note_line[column_key])
        return True
    except (KeyError, ValueError):
        return False
