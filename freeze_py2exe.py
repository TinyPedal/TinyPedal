"""
py2exe build script

Args:
    -c, --clean: force remove old build folder before building.
"""

import argparse
import os
import shutil
import sys
from glob import glob

from py2exe import freeze

from tinypedal import version_check
from tinypedal.const_app import (
    APP_NAME,
    COPYRIGHT,
    PLATFORM,
    VERSION,
)

PYTHON_PATH = sys.exec_prefix
DIST_FOLDER = "dist/"

EXECUTABLE_SETTING = [
    {
        "script": "run.py",
        "icon_resources": [(1, "images/icon.ico")],
        "dest_base": APP_NAME.lower(),
    }
]

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

IMAGE_FILES = [
    "images/CC-BY-SA-4.0.txt",
    "images/icon_compass.png",
    "images/icon_instrument.png",
    "images/icon_steering_wheel.png",
    "images/icon_weather.png",
    "images/icon.png",
]

DOCUMENT_FILES = [
    "docs/changelog.txt",
    "docs/customization.md",
    "docs/contributors.md",
]

LICENSES_FILES = glob("docs/licenses/*")

QT_PLATFORMS = [
    f"{PYTHON_PATH}/Lib/site-packages/PySide2/plugins/platforms/qwindows.dll",
]

QT_MEDIASERVICE = [
    f"{PYTHON_PATH}/Lib/site-packages/PySide2/plugins/mediaservice/dsengine.dll",
    f"{PYTHON_PATH}/Lib/site-packages/PySide2/plugins/mediaservice/wmfengine.dll",
]

BUILD_DATA_FILES = [
    ("", ["LICENSE.txt", "README.md"]),
    ("docs", DOCUMENT_FILES),
    ("docs/licenses", LICENSES_FILES),
    ("images", IMAGE_FILES),
    ("platforms", QT_PLATFORMS),
    ("mediaservice", QT_MEDIASERVICE),
]

BUILD_OPTIONS = {
    "dist_dir": f"{DIST_FOLDER}/{APP_NAME}",
    "excludes": EXCLUDE_MODULES,
    "optimize": 2,
    "compressed": 1,
    # "dll_excludes": ["libcrypto-1_1.dll", "libcrypto-3.dll"],
    # "bundle_files": 2,
}

BUILD_VERSION = {
    "version": VERSION.split("-")[0],  # strip off version tag
    "description": APP_NAME,
    "copyright": COPYRIGHT,
    "product_name": APP_NAME,
    "product_version": VERSION,
}


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
    return parse.parse_args()


def check_dist(build_ready: bool = False) -> bool:
    """Check whether dist folder exist"""
    if not os.path.exists(DIST_FOLDER):
        print("INFO:dist folder not found, creating")
        try:
            os.mkdir(DIST_FOLDER)
            build_ready = True
            print("INFO:dist folder created")
        except (PermissionError, FileExistsError):
            build_ready = False
            print("ERROR:Cannot create dist folder")

    if os.path.exists(DIST_FOLDER):
        build_ready = True
    return build_ready


def check_old_build(clean_build: bool = False, build_ready: bool = False) -> bool:
    """Check whether old build folder exist"""
    if os.path.exists(f"{DIST_FOLDER}{APP_NAME}"):
        print("INFO:Found old build folder")

        if clean_build:
            build_ready = delete_old_build()
            return build_ready

        is_remove = input(
            "INFO:Remove old build folder before building? Yes/No/Quit \n"
        ).lower()

        if "y" in is_remove:
            build_ready = delete_old_build()
        elif "q" in is_remove:
            build_ready = False
        else:
            build_ready = True
            print("WARNING:Building without removing old files")
    return build_ready


def delete_old_build() -> bool:
    """Delete old build folder"""
    try:
        shutil.rmtree(f"{DIST_FOLDER}{APP_NAME}/")
        print("INFO:Old build files removed")
        return True
    except (PermissionError, OSError):
        print("ERROR:Cannot delete build folder")
        return False


def build_exe() -> None:
    """Building executable file"""
    freeze(
        version_info=BUILD_VERSION,
        windows=EXECUTABLE_SETTING,
        options=BUILD_OPTIONS,
        data_files=BUILD_DATA_FILES,
        zipfile="lib/library.zip",
    )


def build_start() -> None:
    """Start building"""
    print("INFO:platform:", PLATFORM.SYSTEM)
    print("INFO:TinyPedal:", VERSION)
    print("INFO:Python:", version_check.python())
    print("INFO:Qt:", version_check.qt())
    print("INFO:PySide:", version_check.pyside())
    print("INFO:psutil:", version_check.psutil())

    if not PLATFORM.WINDOWS:
        print("ERROR:Build script does not support none Windows platform")
        print("INFO:Building canceled")
        return

    cli_args = get_cli_argument()
    if check_old_build(cli_args.clean, check_dist()):
        build_exe()
        print("INFO:Building finished")
    else:
        print("INFO:Building canceled")


build_start()
