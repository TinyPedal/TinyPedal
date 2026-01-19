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
Setting file function
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from time import localtime, monotonic, sleep, strftime
from typing import Callable

from ..const_file import FileExt
from ..setting_validator import PresetValidator

logger = logging.getLogger(__name__)


def set_backup_timestamp(prefix: str = ".backup-", timestamp: bool = True) -> str:
    """Set backup timestamp"""
    if timestamp:
        time_stamp = strftime("%Y-%m-%d-%H-%M-%S", localtime())
    else:
        time_stamp = ""
    return f"{prefix}{time_stamp}"


def copy_setting(dict_user: dict) -> dict:
    """Copy setting"""
    for item in dict_user.values():
        if isinstance(item, dict):
            return {key: item.copy() for key, item in dict_user.items()}
        break
    return dict_user.copy()


def load_setting_json_file(
    filename: str, filepath: str, dict_def: dict, file_info: str = "user preset",
    validator: Callable[[dict, dict], dict] = PresetValidator.user_preset,
) -> dict:
    """Load setting json file & verify"""
    filename_source = f"{filepath}{filename}"
    try:
        with open(filename_source, "r", encoding="utf-8") as jsonfile:
            setting_user = json.load(jsonfile)
        # Verify & assign setting
        setting_user = validator(setting_user, dict_def)
    except FileNotFoundError:
        logger.info("USERDATA: %s not found, fall back to default", filename)
        setting_user = copy_setting(dict_def)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, OSError):
        logger.error("USERDATA: %s failed loading, fall back to default", filename)
        create_backup_file(filename, filepath, set_backup_timestamp(), show_log=True)
        setting_user = copy_setting(dict_def)

    logger.info("USERDATA: %s loaded (%s)", filename, file_info)
    return setting_user


def load_style_json_file(
    filename: str, filepath: str, dict_def: dict, file_info: str = "style preset",
    validator: Callable[[dict], bool] | None = None,
) -> dict:
    """Load style json file & verify (optional)"""
    filename_source = f"{filepath}{filename}"
    msg_text = "loaded"
    try:
        with open(filename_source, "r", encoding="utf-8") as jsonfile:
            style_user = json.load(jsonfile)
        # Whether to validate style
        if validator is not None:
            if validator(style_user):
                create_backup_file(filename, filepath, set_backup_timestamp(), show_log=True)
                msg_text = "updated"
    except FileNotFoundError:
        logger.info("USERDATA: %s not found, fall back to default", filename)
        style_user = copy_setting(dict_def)
        msg_text = "updated"
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, OSError):
        logger.error("USERDATA: %s failed loading, fall back to default", filename)
        create_backup_file(filename, filepath, set_backup_timestamp(), show_log=True)
        style_user = copy_setting(dict_def)
        msg_text = "updated"

    if msg_text == "updated":
        save_json_file(style_user, filename, filepath)

    logger.info("USERDATA: %s %s (%s)", filename, msg_text, file_info)
    return style_user


def save_json_file(
    dict_user: dict, filename: str, filepath: str, extension: str = "", compact_json: bool = False
) -> None:
    """Save json file"""
    filename_source = f"{filepath}{filename}{extension}"
    with open(filename_source, "w", encoding="utf-8") as jsonfile:
        if compact_json:
            json.dump(dict_user, jsonfile, separators=(",", ":"))
        else:
            json.dump(dict_user, jsonfile, indent=4)


def verify_json_file(
    dict_user: dict, filename: str, filepath: str, extension: str = ""
) -> bool:
    """Verify saved json file"""
    filename_source = f"{filepath}{filename}{extension}"
    try:
        with open(filename_source, "r", encoding="utf-8") as jsonfile:
            return json.load(jsonfile) == dict_user
    except FileNotFoundError:
        logger.error("USERDATA: not found %s", filename_source)
    except (ValueError, OSError):
        logger.error("USERDATA: unable to verify %s", filename_source)
    return False


def create_backup_file(
    filename: str, filepath: str, extension: str = FileExt.BAK, show_log: bool = False
) -> bool:
    """Create backup file before saving"""
    filename_source = f"{filepath}{filename}"
    filename_backup = f"{filepath}{filename}{extension}"
    try:
        shutil.copyfile(filename_source, filename_backup)
        if show_log:
            logger.info("USERDATA: backup saved %s", filename_backup)
        return True
    except FileNotFoundError:
        logger.error("USERDATA: not found %s", filename_source)
    except PermissionError:
        logger.error("USERDATA: no permission to access %s", filename_source)
    except OSError:
        logger.error("USERDATA: unable to create backup %s", filename_source)
    return False


def restore_backup_file(
    filename: str, filepath: str, extension: str = FileExt.BAK
) -> bool:
    """Restore backup file if saving failed"""
    filename_backup = f"{filepath}{filename}{extension}"
    filename_source = f"{filepath}{filename}"
    try:
        shutil.copyfile(filename_backup, filename_source)
        logger.info("USERDATA: backup restored %s", filename_source)
        return True
    except FileNotFoundError:
        logger.error("USERDATA: backup not found %s", filename_backup)
    except PermissionError:
        logger.error("USERDATA: no permission to access backup %s", filename_backup)
    except OSError:
        logger.error("USERDATA: unable to restore backup %s", filename_backup)
    return False


def copy_and_rename_backup_file(
    filename: str, filepath: str, extension: str = FileExt.BAK
) -> bool:
    """Copy and rename backup file if restoring backup failed"""
    filename_backup = f"{filepath}{filename}{extension}"
    filename_renamed = f"{filepath}{filename}{set_backup_timestamp()}"
    try:
        shutil.copyfile(filename_backup, filename_renamed)
        logger.info("USERDATA: backup renamed %s", filename_renamed)
        return True
    except FileNotFoundError:
        logger.error("USERDATA: backup not found %s", filename_backup)
    except PermissionError:
        logger.error("USERDATA: no permission to access backup %s", filename_backup)
    except OSError:
        logger.error("USERDATA: unable to copy and rename backup %s", filename_backup)
    return False


def delete_backup_file(
    filename: str, filepath: str, extension: str = FileExt.BAK
) -> bool:
    """Delete backup file"""
    filename_backup = f"{filepath}{filename}{extension}"
    try:
        if os.path.exists(filename_backup):
            os.remove(filename_backup)
        return True
    except FileNotFoundError:
        logger.error("USERDATA: backup not found %s", filename_backup)
    except PermissionError:
        logger.error("USERDATA: no permission to access backup %s", filename_backup)
    except OSError:
        logger.error("USERDATA: unable to delete backup %s", filename_backup)
    return False


def save_and_verify_json_file(
    dict_user: dict,
    filename: str,
    filepath: str,
    max_attempts: int = 10,
    compact_json: bool = False,
) -> None:
    """Save and verify json file, backup or restore if saving failed"""
    file_found = os.path.exists(f"{filepath}{filename}")
    # Create backup: abort saving if backup failed; skip backup and create new if not exist
    if not file_found:
        logger.info("USERDATA: %s not found, create new", filename)
    elif not create_backup_file(filename, filepath):
        logger.info("USERDATA: %s saving abort", filename)
        return
    # Start saving attempts
    attempts = max_attempts
    timer_start = monotonic()
    while attempts > 0:
        save_json_file(dict_user, filename, filepath, compact_json=compact_json)
        if verify_json_file(dict_user, filename, filepath):
            break
        attempts -= 1
        logger.error("USERDATA: %s failed saving, %s attempt(s) left", filename, attempts)
        sleep(0.05)
    timer_end = round((monotonic() - timer_start) * 1000)
    # Clean up
    if attempts > 0:
        state_text = "saved"
    else:
        if file_found and not restore_backup_file(filename, filepath):
            copy_and_rename_backup_file(filename, filepath)
        state_text = "failed saving"
    if file_found:
        delete_backup_file(filename, filepath)
    logger.info(
        "USERDATA: %s %s (took %sms, %s/%s attempts)",
        filename,
        state_text,
        timer_end,
        max_attempts - attempts,
        attempts,
    )
