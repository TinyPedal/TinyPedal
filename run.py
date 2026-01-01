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

import argparse
import os
import sys


def get_cli_argument() -> argparse.Namespace:
    """Get command line argument"""
    parse = argparse.ArgumentParser(
        description="TinyPedal command line arguments",
    )
    parse.add_argument(
        "-l",
        "--log-level",
        choices=range(3),
        default=1,
        type=int,
        help=(
            "set logging output level:"
            " 0 - warning and error only;"
            " 1 - all levels (default);"
            " 2 - output to file;"
        ),
    )
    parse.add_argument(
        "-s",
        "--single-instance",
        choices=range(2),
        default=1,
        type=int,
        help=(
            "set running mode:"
            " 0 - allow running multiple instances;"
            " 1 - single instance (default);"
        ),
    )
    # Disallow version override if run as compiled exe
    if "tinypedal.exe" not in sys.executable:
        parse.add_argument(
            "-p",
            "--pyside",
            choices=(2, 6),
            default=2,
            type=int,
            help=(
                "set PySide (Qt for Python) version:"
                " 2 - PySide2;"
                " 6 - PySide6;"
            ),
        )
    return parse.parse_args()


def override_pyside_version(version: int = 6):
    """Override PySide version 2 to 6"""
    if version != 6:
        return
    original = "PySide2"
    override = f"PySide{version}"
    override_module(original, override)
    override_module(f"{original}.QtCore", f"{override}.QtCore")
    override_module(f"{original}.QtGui", f"{override}.QtGui")
    override_module(f"{original}.QtWidgets", f"{override}.QtWidgets")
    override_module(f"{original}.QtMultimedia", f"{override}.QtMultimedia")


def override_module(original: str, override: str):
    """Manual import & override module"""
    sys.modules[original] = __import__(override, fromlist=[override])


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    # Load command line arguments
    cli_args = get_cli_argument()

    # Check whether to override PySide version
    pyside_override = getattr(cli_args, "pyside", 2)
    os.environ["PYSIDE_OVERRIDE"] = f"{pyside_override}"  # store to env
    override_pyside_version(pyside_override)

    # Start
    from tinypedal.main import start_app

    start_app(cli_args)
