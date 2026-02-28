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
Group configuration keys into labelled sections by word overlap.
"""

class SectionGrouper:
    """Groups configuration keys into labelled sections by word overlap"""

    def __init__(self, min_match: int = 2):
        self.min_match = min_match

    @staticmethod
    def _word_set(phrase: str) -> set[str]:
        """Split underscore-delimited name into word set"""
        return set(phrase.split("_"))

    def _similar(self, topic1: str, topic2: str) -> bool:
        """Check if two topics share enough words to belong in one section"""
        # Direct match if one is a substring of the other
        if topic1 in topic2 or topic2 in topic1:
            return True
        words1 = self._word_set(topic1)
        words2 = self._word_set(topic2)
        return len(words1 & words2) >= self.min_match

    def group_keys(self, keys: list[str]) -> list[tuple[str | None, list[str]]]:
        """Group keys into labelled sections, returns list of (title, key_list) tuples"""
        # Separate column_index_* into its own group
        fixed_groups: dict[str, list[str]] = {}
        remaining: list[str] = []
        for key in keys:
            if key.startswith("column_index_"):
                fixed_groups.setdefault("Column Index", []).append(key)
            else:
                remaining.append(key)

        # Build sections from remaining keys
        sections: list[tuple[str | None, list[str]]] = []
        current_title: str | None = None
        current_keys: list[str] = []
        last_show: str | None = None

        for key in remaining:
            if key.startswith("show_"):
                topic = key[5:]  # strip 'show_' prefix
                if last_show is None:
                    current_title = topic
                    current_keys = [key]
                    last_show = topic
                elif self._similar(last_show, topic):
                    current_keys.append(key)
                    last_show = topic
                else:
                    sections.append((current_title, current_keys))
                    current_title = topic
                    current_keys = [key]
                    last_show = topic
            elif current_title is not None:
                current_keys.append(key)

        # Add last open section
        if current_keys:
            sections.append((current_title, current_keys))

        # Collect keys that appeared before the first show_* key
        all_assigned: set[str] = set()
        for _, key_list in sections:
            all_assigned.update(key_list)
        unassigned = [k for k in remaining if k not in all_assigned]
        if unassigned:
            sections.insert(0, ("", unassigned))

        # Append fixed groups
        for title, fkeys in fixed_groups.items():
            sections.append((title, fkeys))

        return sections
