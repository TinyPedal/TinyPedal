# TinyPedal - racing simulation overlay

TinyPedal is a Free and Open Source telemetry overlay application for racing simulation.

Focuses on minimalist design, light-weight and efficiency, extensive customization and data analysis. Features a large collection of highly configurable overlay widgets and data modules, advanced fuel calculator and editing tools.

Currently supports `rFactor 2` and `Le Mans Ultimate`, and runs on `Windows` and `Linux`.

[Download](https://github.com/TinyPedal/TinyPedal/releases) -
[Quick Start](#quick-start) -
[FAQ](https://github.com/TinyPedal/TinyPedal/wiki/Frequently-Asked-Questions) -
[User Guide](https://github.com/TinyPedal/TinyPedal/wiki/User-Guide) -
[Run on Linux](#running-on-linux) -
[License](#license)
---

![preview](https://user-images.githubusercontent.com/21177177/282278970-b806bf02-a83d-4baa-8b45-0ca10f28f775.png)

## Requirements

TinyPedal requires The Iron Wolf’s `rF2 Shared Memory Map Plugin` from `Download` section of following page:  
https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin

The plugin file `rFactor2SharedMemoryMapPlugin64.dll` should be placed in:

1. For `rFactor 2`, it is `rFactor 2\Bin64\Plugins` folder.

2. For `Le Mans Ultimate`, it is `Le Mans Ultimate\Plugins` folder.

Note, if `Plugins` folder is missing from game folder, you will have to manually create this `Plugins` folder.

This plugin also comes with some of the popular rF2/LMU Apps, check corresponding game's plugins folder first to see if it was installed already.

In-game setup:

1. Set game display mode to `Borderless` or `Windowed` mode. `Fullscreen` mode is not supported.

2. Enable shared memory map plugin:

    For `rFactor 2`, in game `Settings` -> `Gameplay` page, find `Plugins` section and toggle on `rFactor2SharedMemoryMapPlugin64.dll`.

    For `Le Mans Ultimate`, user may have to manually enable plugin by editing `CustomPluginVariables.JSON` file (set `" Enabled"` value to `1` ) under `Le Mans Ultimate\UserData\player` folder.

    After plugin enabled, must `restart game` to take effect.

    Note, if game cannot generate `rFactor2SharedMemoryMapPlugin64.dll` entry in `CustomPluginVariables.JSON` file, make sure `VC12 (Visual C++ 2013) runtime` is installed, which can be found in game's `Support\Runtimes` folder.

## Quick Start

**Important:** make sure required plugins are installed as mentioned in [Requirements](#requirements) section.

1. Download latest TinyPedal version from [Releases](https://github.com/TinyPedal/TinyPedal/releases) page, extract it into a clean folder, and run `tinypedal.exe`.  
Note, DO NOT extract TinyPedal into `system` or `game` folder, such as `Program Files` or `rFactor 2` folder, otherwise it may fail to run.  
Alternatively, run TinyPedal from source, see [Run from source](#run-from-source) section for details.  
For Linux user, please follow [Running on Linux](#running-on-linux) section for instruction.  

2. A tray icon will appear at system tray. If not shown, check hidden tray icon. `Right Click` on tray icon will bring up context menu.

3. Launch game, overlay will appear once vehicle is on track, and auto-hide otherwise. Auto-hide can be toggled On and Off by clicking `Auto Hide` from tray menu.

4. Overlay can be Locked or Unlocked by clicking `Lock Overlay` from tray menu. While Unlocked, click on overlay to drag around.

5. Widgets can be Enabled or Disabled from `Widget` panel in main window. `Right Click` on tray icon and select `Config` to show main window if it is hidden.

6. To quit APP, `Right Click` on tray icon and select `Quit`; or, click `Overlay` menu from main window and select `Quit`.

See [Frequently Asked Questions](https://github.com/TinyPedal/TinyPedal/wiki/Frequently-Asked-Questions) for common issues.

See [User Guide](https://github.com/TinyPedal/TinyPedal/wiki/User-Guide) for usage info.

## Run from source

### Dependencies:
* [Python](https://www.python.org/) 3.8, 3.9, or 3.10
* PySide2
* pyRfactor2SharedMemory
* psutil

Note, PySide2 may not be available for Python version higher than 3.10; or requires PySide6 instead for running with newer Python version. PySide6 is currently supported only via command line argument, see `Command line arguments` section in `User Guide` for details.

### Steps:

1. Download source code from [Releases](https://github.com/TinyPedal/TinyPedal/releases) page; or click `Code` button at the top of repository and select `Download ZIP`; or use `Git` tool to clone this repository.

2. Download submodule `pyRfactor2SharedMemory` source code from:  
https://github.com/s-victor/pyRfactor2SharedMemory  
(This forked version includes a few required changes for TinyPedal)

3. Extract TinyPedal source code ZIP file. Then extract pyRfactor2SharedMemory ZIP file and put `pyRfactor2SharedMemory` folder in the root folder of TinyPedal.

4. Install additional dependencies by using command:  
`pip3 install PySide2 psutil`  

5. To start TinyPedal, type command from root folder:  
`python run.py`  
(TinyPedal is currently tested on Python 3.8+)

Note: if using `Git` tool to clone this repository, run command with `--recursive` to also clone submodule, such as:  
`git clone --recursive https://github.com/TinyPedal/TinyPedal.git`

## Build executable for Windows

Executable file can be built with [py2exe](http://www.py2exe.org).

To install py2exe, run command:  
`pip3 install py2exe`

To build executable file, run command:  
`python freeze_py2exe.py`

After building completed, executable file can be found in `dist\TinyPedal` folder.

Note: the build script only supports py2exe `v0.12.0.0` or higher.

## Running on Linux

The procedure described in the [Run from source](#run-from-source) section is mostly valid,
except some differences in the dependencies, and that no executable can be
built. The differences are explained here.

Configuration and data files will be stored in the defined user-specific
directories, usually at `$HOME/.config/TinyPedal/` and
`$HOME/.local/share/TinyPedal/` respectively.

The required Python packages are `PySide2`, `psutil` and `pyxdg`. Most distros
name the package with a prefix, like `python3-pyside2`, `python3-psutil` and
`python3-pyxdg`.

Some distros split `PySide2` in subpackages. If you don't find
`python3-pyside2` then you should install `python3-pyside2.qtgui`,
`python3-pyside2.qtwidgets` and `python3-pyside2.qtmultimedia`.

Alternatively, you can install them using `pip3` but this will bypass your
system package manager and it isn't the recommended option. The command to
install the dependencies with this method is:

`pip3 install PySide2 psutil pyxdg`

The Iron Wolf's rF2 Shared Memory Map Plugin has to be replaced with [this fork
for
Wine](https://github.com/schlegp/rF2SharedMemoryMapPlugin_Wine/blob/master/build).

To start TinyPedal type the following command:  
`./run.py`

### Installation

Once you have a working instance of TinyPedal, created using the git command or
by unpacking the Linux release file, you can run the install script to install
or update TinyPedal on your system.

The install script will create a desktop launcher and will make `TinyPedal`
available as a command from the terminal.

The files will be installed at the `/usr/local/` prefix. You'll need
appropriate permissions to write there, for example, by using `sudo`.

You can run the script as (it doesn't support any arguments or options):  
`sudo ./install.sh`

### Known issues

- Widgets don't appear over the game window in KDE. Workaround: enable `Bypass Window Manager` option in `Compatibility` dialog from `Config` menu in main window.
- Transparency of widgets doesn't work when desktop compositing is disabled. Workaround: enable `window manager compositing` in your DE.

## License

Copyright (C) 2022-2025 TinyPedal developers

TinyPedal is free software and licensed under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. TinyPedal is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY. See [LICENSE.txt](./LICENSE.txt) for more info.

TinyPedal icon, as well as image files located in `images` folder, are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Licenses and notices file for third-party software are located in `docs\licenses` folder, see [THIRDPARTYNOTICES.txt](./docs/licenses/THIRDPARTYNOTICES.txt) file for details.

## Credits

See [docs\contributors.md](./docs/contributors.md) file for full list of developers and contributors.
