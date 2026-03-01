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

"""Group config keys into labelled sections by word overlap"""


class ConfigGrouper:
    """Group keys into sections based on show_* prefixes and word similarity"""

    # Constants for packing
    MAX_TABLE_ROWS = 12
    MIN_REMAINING_ROWS = 4

    def __init__(self, min_match=2):
        self.min_match = min_match

    def _are_topics_similar(self, topic_a, topic_b):
        """Check if two topics share enough words or are substrings"""
        if topic_a in topic_b or topic_b in topic_a:
            return True
        words_a = set(topic_a.split("_"))
        words_b = set(topic_b.split("_"))
        return len(words_a & words_b) >= self.min_match

    def group_keys(self, keys):
        """Group keys into (title, key_list) sections"""
        fixed_groups = {}
        for key in keys:
            if key.startswith("column_index_"):
                fixed_groups.setdefault("Column Index", []).append(key)
        fixed_set = {k for group in fixed_groups.values() for k in group}
        remaining = [k for k in keys if k not in fixed_set]
        # Build dynamic sections from show_* keys
        sections = []
        current_title = None
        current_keys = []
        last_show_topic = None
        for key in remaining:
            if key.startswith("show_"):
                topic = key[5:]
                if current_title is None:
                    current_title = topic
                    current_keys = [key]
                    last_show_topic = topic
                elif self._are_topics_similar(last_show_topic, topic):
                    current_keys.append(key)
                    last_show_topic = topic
                else:
                    sections.append((current_title, current_keys))
                    current_title = topic
                    current_keys = [key]
                    last_show_topic = topic
            else:
                if current_title is not None:
                    current_keys.append(key)
        if current_keys:
            sections.append((current_title, current_keys))
        # Keys before first show_* go into untitled section
        assigned = set()
        for _, key_list in sections:
            assigned.update(key_list)
        unassigned = [k for k in remaining if k not in assigned]
        if unassigned:
            sections = [("", unassigned)] + sections
        # Add fixed groups
        for title, fkeys in fixed_groups.items():
            sections.append((title, fkeys))
        return sections

    def pack_sections(self, sections_data, max_rows=None, min_remaining=None):
        """Pack sections into batches that fit in tables of max_rows rows.

        Parameters
        ----------
        sections_data : list of (title, keys)
            Sections to pack.
        max_rows : int, optional
            Maximum rows per table. Defaults to class constant.
        min_remaining : int, optional
            Minimum remaining rows to start a new table. Defaults to class constant.

        Returns
        -------
        list of list of (title, keys)
            Batches, each suitable for one merged table.
        """
        if max_rows is None:
            max_rows = self.MAX_TABLE_ROWS
        if min_remaining is None:
            min_remaining = self.MIN_REMAINING_ROWS

        batches = []
        current_batch = []
        current_rows = 0

        for title, sec_keys in sections_data:
            section_size = len(sec_keys) + 1  # keys + header
            remaining = max_rows - current_rows
            if current_batch and (
                remaining < min_remaining
                or current_rows + section_size > max_rows
            ):
                batches.append(current_batch)
                current_batch = []
                current_rows = 0
            current_batch.append((title, sec_keys))
            current_rows += section_size

        if current_batch:
            batches.append(current_batch)

        return batches

    def _get_min_column_index(self, widget, current_values):
        """Return the minimum column_index value among keys in the widget's section_keys property.

        Parameters
        ----------
        widget : QWidget
            Widget that has a property "section_keys" (list of keys).
        current_values : dict
            Current values mapping key -> value.

        Returns
        -------
        int
            Minimum index, or a large number if none.
        """
        keys = widget.property("section_keys") or []
        min_idx = 999999
        for key in keys:
            if key.startswith("column_index_"):
                val = current_values.get(key, 999999)
                if isinstance(val, (int, float)):
                    min_idx = min(min_idx, val)
        return min_idx

    def sort_widgets_by_column_index(self, widgets, current_values):
        """Sort a list of widgets in-place by their minimum column index.

        Parameters
        ----------
        widgets : list of QWidget
            Widgets to sort (must have "section_keys" property).
        current_values : dict
            Current values mapping key -> value.
        """
        widgets.sort(key=lambda w: self._get_min_column_index(w, current_values))
