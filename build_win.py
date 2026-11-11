"""
py2exe build script for TinyPedal on Windows

PySide2 requires:
- Python 3.8, 3.9, 3.10
- py2exe <=0.13.0.2, >=0.12.0.0 (>=0.14 doesn't work with Python 3.8, 3.9)

PySide6 requires:
- Python >=3.10
- py2exe >=0.13.0.2
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from glob import glob

import py2exe

from tinypedal import argument, override_pyside_version, version_check
from tinypedal.constant import APP, FILE, PLATFORM


def get_cli_argument():
    """Get command line argument"""
    arg_pyside = argument.add_argument(
        name="pyside",
        arguments=("-p", "--pyside"),
        choices=(2, 6),
        default=2,
        help="set PySide version to build; '2' PySide2 (default); '6' PySide6",
    )
    arg_clean = argument.add_argument(
        name="clean",
        arguments=("-c", "--clean"),
        help="force clean build; remove old build folder before building",
    )
    arg_output = argument.add_argument(
        name="output",
        arguments=("-o", "--output"),
        default="dist",
        help="set output build folder for distribution files, default to './dist'",
    )
    cli_args = argument.parse_argument(
        headline="TinyPedal windows executable build command line arguments",
        exe_name=os.path.basename(__file__),
        user_arguments=sys.argv,
        app_arguments=(
            arg_pyside,
            arg_clean,
            arg_output,
        ),
    )
    return cli_args


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


def check_build_info(dist_path: str) -> None:
    """Check build info"""
    print("INFO:py2exe:", py2exe.__version__)
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
        sys.exit()


def build_exe_pyside2(dist_path: str) -> None:
    """Building executable file with PySide2"""
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
        "PySide6",  # in case both PySide2 & PySide6 installed
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
        "argparse",
        "optparse",
        "tarfile",
        "doctest",
        "configparser",
        "plistlib",
        "pickle",
    ]
    if sys.version_info < (3, 10):
        EXCLUDE_MODULES += [
            # Not required on python 3.8, 3.9
            "urllib",
            "pathlib",
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
        #f"{PYTHON_PATH}/Lib/site-packages/PySide2/plugins/mediaservice/dsengine.dll",
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
    py2exe.freeze(
        version_info=BUILD_VERSION,
        windows=EXECUTABLE_SETTING,
        options=BUILD_OPTIONS,
        data_files=BUILD_DATA_FILES,
        zipfile="lib/library.zip",
    )


def build_exe_pyside6(dist_path: str) -> None:
    """Building executable file with PySide6"""
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

    pyside_version = cli_args.get("pyside", 2)
    override_pyside_version(pyside_version)

    check_build_info(dist_path)

    if check_old_build(cli_args.get("clean", False), dist_path):
        if pyside_version != 6:
            build_exe_pyside2(dist_path)
        else:
            build_exe_pyside6(dist_path)
        print("INFO:Building finished")
    else:
        print("INFO:Building canceled")


if __name__ == "__main__":
    # Add search path for third party modules
    sys.path.append("thirdparty")

    build_start()
