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


# Argument function
def add_argument(name: str, arguments: tuple[str, ...], choices: tuple[int, ...], default: int | None, help: str) -> dict:
    """Add argument"""
    return {
        "name": name,
        "arguments": arguments,
        "choices": choices,
        "default": default,
        "help": help,
    }


def format_argument(arg: dict, padding=30) -> str:
    """Format argument"""
    arg_text = ', '.join(arg["arguments"])
    choices = arg["choices"]
    help_text = arg["help"]
    if choices:
        arg_text += f" [{','.join(str(v) for v in choices)}]"
    return f"  {arg_text:<{padding}}  {help_text}\n"


def print_help(desc: str, exe_name: str, help_arg: dict, app_args: tuple[dict, ...], error_arg: str | None = None):
    """Print command line help info"""
    # Print option
    file = sys.stdout
    file.write(f"Usage: {exe_name} [OPTION] ...\n")
    if desc:
        file.write(f"{desc}\n")
    file.write("\n")
    file.write(format_argument(help_arg))
    long_ver = ""
    short_ver = ""
    for arg_info in app_args:
        file.write(format_argument(arg_info))
        arguments = arg_info["arguments"]
        choices = arg_info["choices"]
        if choices:
            long_ver += f"{arguments[-1]} {choices[-1]} "
            short_ver += f"{arguments[0]} {choices[0]} "
        else:
            long_ver += f"{arguments[-1]} "
            short_ver += f"{arguments[0]} "
    # Print example
    file.write("\nExample:\n")
    file.write(f"    {exe_name} {long_ver}\n")
    file.write(f"    {exe_name} {short_ver}\n")
    # Print error
    if error_arg is not None:
        file.write(f"\nError: invaild arguments: '{error_arg}'")


def parse_argument(desc: str, exe_name: str, user_arguments: list[str], app_arguments: tuple[dict, ...]) -> dict:
    """Parse command line argument"""
    args_output = {}
    if len(user_arguments) < 2:
        return args_output

    # Split arguments
    user_args = [_arg for text in user_arguments[1:] for _arg in text.split(" ") if _arg]

    # Check help argument first
    help_arg = add_argument(
        name="help",
        arguments=("-h", "--help"),
        choices=(),
        default=None,
        help="show this help message and exit",
    )
    # Check optional arguments
    try:
        temp_arg = None
        for args in help_arg["arguments"]:
            if args in user_args:
                raise ValueError

        skip_next = False
        for index, user_arg in enumerate(user_args):
            temp_arg = ""
            if skip_next:
                skip_next = False
                continue

            # Match next argument
            for arg_info in app_arguments:
                if user_arg in arg_info["arguments"]:
                    break
            else:
                temp_arg = user_arg
                raise ValueError

            default = arg_info["default"]

            # Without choices
            if default is None:
                args_output[arg_info["name"]] = True
                continue

            # With choices
            skip_next = True
            temp_arg = user_args[index + 1]
            temp_value = type(default)(temp_arg)
            if temp_value in arg_info["choices"]:
                args_output[arg_info["name"]] = temp_value
            else:
                raise ValueError

    except (TypeError, IndexError, KeyError, ValueError):
        print_help(desc, exe_name, help_arg, app_arguments, temp_arg)
        sys.exit()

    return args_output


# Module override function
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


# General function
def int_signal_handler(sign, frame):
    """Quit by keyboard interrupt"""
    sys.exit()


def main():
    """Run app"""
    # Check whether running from source
    exe_name = "tinypedal.exe"
    if exe_name not in sys.executable:
        exe_name = "python run.py"
        os.environ["RUN_FROM_SOURCE"] = "TRUE"

        # Add keyboard interrupt signal
        import signal
        signal.signal(signal.SIGINT, int_signal_handler)

        # Add search path for third party modules
        sys.path.append("thirdparty")

    # Config arguments
    arg_log_level = add_argument(
        name="log_level",
        arguments=("-l", "--log-level"),
        choices=(0, 1, 2),
        default=1,
        help="set logging output level; '0' error only; '1' all (default); '2' to file",
    )
    arg_single_instance = add_argument(
        name="single_instance",
        arguments=("-s", "--single-instance"),
        choices=(0, 1),
        default=1,
        help="set running mode:; '0' allow multiple instances; '1' single instance (default)",
    )
    arg_pyside = add_argument(
        name="pyside",
        arguments=("-p", "--pyside"),
        choices=(2, 6),
        default=2,
        help="set PySide version; '2' PySide2 (default); '6' PySide6 (source only)",
    )

    # Load command line arguments
    cli_args = parse_argument(
        desc="TinyPedal command line arguments",
        exe_name=exe_name,
        user_arguments=sys.argv,
        app_arguments=(
            arg_log_level,
            arg_single_instance,
            arg_pyside,
        ),
    )
    opt_log_level = cli_args.get("log_level", arg_log_level["default"])
    opt_single_instance = cli_args.get("single_instance", arg_single_instance["default"]) != 0
    opt_pyside_override = cli_args.get("pyside", arg_pyside["default"])

    # Check whether to override PySide version
    override_pyside_version(opt_pyside_override)
    os.environ["PYSIDE_OVERRIDE"] = str(opt_pyside_override)

    # Start
    import tinypedal

    tinypedal.start(
        log_level=opt_log_level,
        single_instance=opt_single_instance,
    )


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    main()

    # Start main loop only after main function exits (so temp vars are garbage collected)
    from PySide2.QtWidgets import QApplication

    if os.getenv("PYSIDE_OVERRIDE") == "6":  # use 'exec' for pyside6
        sys.exit(QApplication.instance().exec())
    else:
        sys.exit(QApplication.instance().exec_())
