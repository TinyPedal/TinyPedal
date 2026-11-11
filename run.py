#!/usr/bin/env python3

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
Run program
"""

from __future__ import annotations

import os
import sys

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    import tinypedal

    tinypedal.start()

    # Start main loop only after main function exits (so temp vars are garbage collected)
    from PySide2.QtWidgets import QApplication

    if os.getenv("PYSIDE_OVERRIDE") == "6":  # use 'exec' for pyside6
        sys.exit(QApplication.instance().exec())
    else:
        sys.exit(QApplication.instance().exec_())
