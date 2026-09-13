"""
py2exe build script
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from glob import glob

from py2exe import freeze

from tinypedal import version_check
from tinypedal.constant import APP, FILE, PLATFORM


def get_cli_argument():
    """Get command line argument"""
    parse = argparse.ArgumentParser(
        description="TinyPedal windows excutable build command line arguments"
    )
    parse.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="force remove old build folder before building",
    )
    parse.add_argument(
        "-p",
        "--path",
        type=str,
        default="dist",
        help="set build folder for distribution files, default to './dist'",
    )
    return parse.parse_args()


def check_dist(dist_path: str) -> str:
    """Check whether build folder exist"""
    dist_path = dist_path.strip().replace("\\", "/")

    if not dist_path:
        print("ERROR:Build path cannot be empty")
        return ""

    if re.search(r'[:*?"<>|]', dist_path) is not None:
        print("ERROR:Build path cannot contain following characters:\n: * ? < > |")
        return ""

    if not dist_path.endswith("/"):
        dist_path += "/"

    if os.path.exists(dist_path):
        return dist_path

    print("INFO:build folder not found, creating")
    try:
        os.mkdir(dist_path)
        print("INFO:build folder created")
        return dist_path
    except (PermissionError, FileExistsError):
        print("ERROR:Cannot create build folder")
    return ""


def check_old_build(clean_build: bool, dist_path: str) -> bool:
    """Check whether old build folder exist"""
    if not os.path.exists(f"{dist_path}{APP.TINYPEDAL}"):
        return True

    print("INFO:Found old build folder")

    if clean_build:
        return delete_old_build(dist_path)

    is_remove = input(
        "INFO:Remove old build folder before building? Yes/No/Quit \n"
    ).lower()

    if "y" in is_remove:
        return delete_old_build(dist_path)
    if "q" in is_remove:
        return False
    print("WARNING:Building without removing old files")
    return True


def delete_old_build(dist_path: str) -> bool:
    """Delete old build folder"""
    try:
        shutil.rmtree(f"{dist_path}{APP.TINYPEDAL}/")
        print("INFO:Old build files removed")
        return True
    except (PermissionError, OSError):
        print("ERROR:Cannot delete build folder")
        return False


def build_exe(dist_path: str) -> None:
    """Building executable file"""
    PYTHON_PATH = sys.exec_prefix
    # ---------------------------------------------------
    BUILD_VERSION = {
        "version": APP.VERSION.split("-")[0],  # strip off version tag
        "description": APP.TINYPEDAL,
        "copyright": APP.COPYRIGHT,
        "product_name": APP.TINYPEDAL,
        "product_version": APP.VERSION,
    }
    # ---------------------------------------------------
    EXECUTABLE_SETTING = [
        {
            "script": "run.py",
            "icon_resources": [(1, FILE.IMAGE_ICON)],
            "dest_base": APP.TINYPEDAL.lower(),
        }
    ]
    # ---------------------------------------------------
    EXCLUDE_MODULES = [
        "difflib",
        "pdb",
        "venv",
        "tkinter",
        "curses",
        "distutils",
        "lib2to3",
        "unittest",
        "xmlrpc",
        "multiprocessing",
        # "_ssl",
        # "ssl",
        # "email",
        # "http",
        # "urllib",
    ]
    BUILD_OPTIONS = {
        "dist_dir": f"{dist_path}/{APP.TINYPEDAL}",
        "excludes": EXCLUDE_MODULES,
        "optimize": 2,
        "compressed": 1,
        # "dll_excludes": ["libcrypto-1_1.dll", "libcrypto-3.dll"],
        # "bundle_files": 2,
    }
    # ---------------------------------------------------
    APP_FILES = [
        FILE.DOC_LICENSE,
        FILE.DOC_README,
    ]
    IMAGE_FILES = [
        f"{FILE.PATH_IMAGE}CC-BY-SA-4.0.txt",
        FILE.IMAGE_COMPASS,
        FILE.IMAGE_INSTRUMENT,
        FILE.IMAGE_STEERING_WHEEL,
        FILE.IMAGE_WEATHER,
        FILE.IMAGE_TINYPEDAL,
    ]
    DOCUMENT_FILES = [
        FILE.DOC_CHANGELOG,
        FILE.DOC_USERGUIDE,
        FILE.DOC_CONTRIBUTORS,
    ]
    QT_PLATFORMS = [
        f"{PYTHON_PATH}/Lib/site-packages/PySide2/plugins/platforms/qwindows.dll",
    ]
    QT_MEDIASERVICE = [
        f"{PYTHON_PATH}/Lib/site-packages/PySide2/plugins/mediaservice/dsengine.dll",
        f"{PYTHON_PATH}/Lib/site-packages/PySide2/plugins/mediaservice/wmfengine.dll",
    ]
    BUILD_DATA_FILES = [
        ("", APP_FILES),
        (FILE.PATH_DOC, DOCUMENT_FILES),
        (FILE.PATH_THIRDPARTYLICENSES, glob(f"{FILE.PATH_THIRDPARTYLICENSES}*")),
        (FILE.PATH_IMAGE, IMAGE_FILES),
        ("platforms", QT_PLATFORMS),
        ("mediaservice", QT_MEDIASERVICE),
    ]
    # ---------------------------------------------------
    freeze(
        version_info=BUILD_VERSION,
        windows=EXECUTABLE_SETTING,
        options=BUILD_OPTIONS,
        data_files=BUILD_DATA_FILES,
        zipfile="lib/library.zip",
    )


def build_start() -> None:
    """Start building"""
    cli_args = get_cli_argument()
    dist_path = check_dist(cli_args.path)
    if not dist_path:
        print("INFO:Building canceled")
        return

    print("INFO:Build path:", os.path.abspath(dist_path))
    print("INFO:Platform:", PLATFORM.SYSTEM)
    print("INFO:TinyPedal:", APP.VERSION)
    print("INFO:Python:", version_check.python())
    print("INFO:Qt:", version_check.qt())
    print("INFO:PySide:", version_check.pyside())
    print("INFO:psutil:", version_check.psutil())

    if not PLATFORM.WINDOWS:
        print("ERROR:Build script does not support none Windows platform")
        print("INFO:Building canceled")
        return

    if check_old_build(cli_args.clean, dist_path):
        build_exe(dist_path)
        print("INFO:Building finished")
    else:
        print("INFO:Building canceled")


build_start()
