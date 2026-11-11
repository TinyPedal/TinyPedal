"""
py2exe build script for PySide6

Requires:
- Python >=3.10
- py2exe >=0.13.0.2
"""

from __future__ import annotations

import sys
from glob import glob

import py2exe

from freeze_pyside2 import (
    check_build_info,
    check_dist,
    check_old_build,
    get_cli_argument,
)
from tinypedal import override_pyside_version
from tinypedal.constant import APP, FILE


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
        "PySide2",  # in case both PySide2 & PySide6 installed
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
        "thirdparty",
        # "_ssl",
        # "ssl",
        "xml",
        "email",
        "http",
        "_pydecimal",
        "lzma",
        "bz2",
        "calendar",
        "getopt",
        "optparse",
        "tarfile",
        "doctest",
        "configparser",
        "plistlib",
        "pickle",
        # Required by pyside6
        # "pathlib",
        # "argparse",
    ]
    if sys.version_info >= (3, 13):
        EXCLUDE_MODULES += [
            # Not required on python 3.13+
            "urllib",
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
        f"{PYTHON_PATH}/Lib/site-packages/PySide6/plugins/platforms/qwindows.dll",
    ]
    QT_MULTIMEDIA = [
        #f"{PYTHON_PATH}/Lib/site-packages/PySide6/plugins/multimedia/ffmpegmediaplugin.dll",
        f"{PYTHON_PATH}/Lib/site-packages/PySide6/plugins/multimedia/windowsmediaplugin.dll",
    ]
    BUILD_DATA_FILES = [
        ("", APP_FILES),
        (FILE.PATH_DOC, DOCUMENT_FILES),
        (FILE.PATH_THIRDPARTYLICENSES, glob(f"{FILE.PATH_THIRDPARTYLICENSES}*")),
        (FILE.PATH_IMAGE, IMAGE_FILES),
        ("platforms", QT_PLATFORMS),
        ("multimedia", QT_MULTIMEDIA),
    ]
    # ---------------------------------------------------
    py2exe.freeze(
        version_info=BUILD_VERSION,
        windows=EXECUTABLE_SETTING,
        options=BUILD_OPTIONS,
        data_files=BUILD_DATA_FILES,
        zipfile="lib/library.zip",
    )


def build_start() -> None:
    """Start building"""
    cli_args = get_cli_argument()
    dist_path = check_dist(cli_args.get("output", "dist"))
    if not dist_path:
        print("INFO:Building canceled")
        return

    check_build_info(dist_path)

    if check_old_build(cli_args.get("clean", False), dist_path):
        build_exe(dist_path)
        print("INFO:Building finished")
    else:
        print("INFO:Building canceled")


if __name__ == "__main__":
    # Use pyside6
    override_pyside_version(6)

    # Add search path for third party modules
    sys.path.append("thirdparty")

    build_start()
