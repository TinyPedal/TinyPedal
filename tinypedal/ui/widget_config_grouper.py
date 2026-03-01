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
Widget config key grouper

Groups widget config keys into labelled sections by show_* prefixes and word similarity.
Used by WidgetConfig to split widget options into logical sections.
"""


class WidgetConfigGrouper:
    """Group keys into sections based on show_* prefixes and word similarity"""

    def __init__(self, min_match=2):
        # min_match: minimum shared words to consider two topics similar
        pass

    def group_keys(self, keys):
        # Split keys into (title, key_list) sections:
        # 1. column_index_* keys -> "Column Index" group
        # 2. Keys before first show_* -> untitled general group ("")
        # 3. show_* keys + trailing non-show keys -> named sections
        #
        # Named sections are grouped by topic similarity:
        # - show_speed and show_speed_limit -> same section
        # - show_fuel and show_tire -> different sections
        #
        # Returns: list of (title, key_list) tuples
        pass

    def _are_topics_similar(self, topic_a, topic_b):
        # Check if two topics share enough words or are substrings
        # "speed" in "speed_limit" -> True
        # {"speed"} & {"speed", "limit"} >= min_match -> True
        pass
