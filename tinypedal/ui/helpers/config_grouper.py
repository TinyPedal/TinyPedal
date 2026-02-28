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
