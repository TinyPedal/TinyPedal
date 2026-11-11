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
Argument function
"""

from __future__ import annotations

import sys


def add_argument(
    name: str,
    arguments: tuple[str, ...],
    choices: tuple[int, ...] = (),
    default: int | None = None,
    help: str = "",
) -> dict:
    """Add argument

    Args:
        name: argument key name.
        arguments: short and/or long argument name, for example ("-o", "--output").
        choices: optional argument value choice (tuple), for example (0, 1, 2).
        default: optional argument default value.
        help: help text.
    """
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


def print_argument(
    desc: str,
    exe_name: str,
    help_arg: dict,
    app_args: tuple[dict, ...],
    error_arg: str | None = None,
):
    """Print command line arguments help info"""
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
        default = arg_info["default"]
        if default is not None:
            long_ver += f"{arguments[-1]} {default} "
            short_ver += f"{arguments[0]} {default} "
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


def parse_argument(
    headline: str,
    exe_name: str,
    user_arguments: list[str],
    app_arguments: tuple[dict, ...],
) -> dict:
    """Parse command line arguments

    Args:
        headline: headline description.
        exe_name: executable file name.
        user_arguments: user arguments.
        app_arguments: app available arguments.
    """
    args_output = {}
    if len(user_arguments) < 2:
        return args_output

    # Split arguments
    user_args = [_arg for text in user_arguments[1:] for _arg in text.split(" ") if _arg]

    # Check help argument first
    help_arg = add_argument(
        name="help",
        arguments=("-h", "--help"),
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

            # Without default (boolean)
            if default is None:
                args_output[arg_info["name"]] = True
                continue

            # With choices or default
            skip_next = True
            temp_arg = user_args[index + 1]
            temp_value = type(default)(temp_arg)
            if temp_value in arg_info["choices"] or not arg_info["choices"]:
                args_output[arg_info["name"]] = temp_value
            else:
                raise ValueError

    except (TypeError, IndexError, KeyError, ValueError):
        print_argument(headline, exe_name, help_arg, app_arguments, temp_arg)
        sys.exit()

    return args_output
