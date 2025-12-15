#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Pace notes view & player
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from PySide2.QtCore import QBasicTimer, Qt, QUrl
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .. import realtime_state
from ..api_control import api
from ..const_file import FileFilter
from ..module_control import mctrl
from ..module_info import minfo
from ..setting import cfg
from ..userfile import set_relative_path
from ..userfile.track_notes import COLUMN_PACENOTE
from ._common import CompactButton, UIScaler

logger = logging.getLogger(__name__)


class PaceNotesPlayer(QMediaPlayer):
    """Pace notes player"""

    def __init__(self, parent, config: dict):
        super().__init__(parent)
        self.mcfg = config
        self.is_pyside6 = os.getenv("PYSIDE_OVERRIDE") == "6"
        self.audio_device = self.set_audio_device()

        # Set update timer
        self._update_timer = QBasicTimer()

        # Last data
        self._checked = False
        self._last_notes_index = None
        self._play_queue: list[str] = []

    def set_audio_device(self):
        """Set audio device"""
        if self.is_pyside6:
            from PySide6.QtMultimedia import QAudioOutput

            audio_device = QAudioOutput()
            self.setAudioOutput(audio_device)  # qt6 only
            return audio_device
        return None  # qt5

    def set_playback(self, enabled: bool):
        """Set playback state"""
        self.reset_playback()
        if enabled:
            update_interval = max(
                self.mcfg["update_interval"],
                cfg.application["minimum_update_interval"],
            )
            self._update_timer.start(update_interval, self)
            logger.info("ENABLED: pace notes sounds playback")
        else:
            self._update_timer.stop()
            logger.info("DISABLED: pace notes sounds playback")

    def reset_playback(self):
        """Reset"""
        self._checked = False
        self._last_notes_index = None
        self._play_queue.clear()
        self.stop()
        self.set_volume(self.mcfg["pace_notes_sound_volume"])

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if realtime_state.active:

            # Reset switch
            if not self._checked:
                self._checked = True

            # Playback
            notes_index = minfo.pacenotes.currentIndex
            if self._last_notes_index != notes_index:
                self._last_notes_index = notes_index
                if self.mcfg["enable_playback_while_in_pit"] or not api.read.vehicle.in_pits():
                    self.__update_queue(minfo.pacenotes.currentNote.get(COLUMN_PACENOTE))

            if self._play_queue:
                self.__play_next_in_queue()

        else:
            if self._checked:
                self.reset_playback()

    def set_source(self) -> None:
        """Set source (compatibility)"""
        # Get sound source url
        pace_note = self._play_queue[0]
        sound_path = self.mcfg["pace_notes_sound_path"]
        sound_format = self.mcfg["pace_notes_sound_format"].strip(".")
        source_url = QUrl(f"{sound_path}{pace_note}.{sound_format}")

        if self.is_pyside6:
            return self.setSource(source_url)  # qt6
        return self.setMedia(source_url)  # qt5

    def set_volume(self, value: int) -> None:
        """Set volume (compatibility)"""
        if self.is_pyside6 and self.audio_device:
            return self.audio_device.setVolume(value / 100)  # qt6 (0.0 - 1.0)
        return self.setVolume(value)  # qt5 (0 - 100)

    def is_playing(self) -> bool:
        """Is playing state (compatibility)"""
        if self.is_pyside6:
            return self.playbackState() == QMediaPlayer.PlayingState  # qt6
        return self.state() == QMediaPlayer.State.PlayingState  # qt5

    def __update_queue(self, pace_note: str | None):
        """Update playback queue"""
        if (pace_note is not None
            and len(self._play_queue) < self.mcfg["pace_notes_sound_max_queue"]):
            self._play_queue.append(pace_note)

    def __play_next_in_queue(self):
        """Play next sound in playback queue"""
        # Wait if is playing & not exceeded max duration
        if (self.is_playing() and
            self.position() < self.mcfg["pace_notes_sound_max_duration"] * 1000):
            return
        # Play next sound in queue
        self.set_source()
        self.play()
        self._play_queue.pop(0)  # remove playing notes from queue


class PaceNotesControl(QWidget):
    """Pace notes control"""

    def __init__(self, parent, notify_toggle: Callable):
        super().__init__(parent)
        self.notify_toggle = notify_toggle
        self.mcfg = cfg.user.setting["pace_notes_playback"]
        self.pace_notes_player = PaceNotesPlayer(self, self.mcfg)

        # Pace notes file selector
        self.checkbox_file = QCheckBox("Manually Select Pace Notes File")
        self.checkbox_file.toggled.connect(self.toggle_selector_state)

        self.file_selector = QLineEdit()
        self.file_selector.setReadOnly(True)
        self.button_openfile = CompactButton("Open")
        self.button_openfile.clicked.connect(self.set_notes_path)

        # Sound path selector
        label_path = QLabel("Sound File Path:")
        self.path_selector = QLineEdit()
        self.path_selector.setReadOnly(True)
        button_openpath = CompactButton("Open")
        button_openpath.clicked.connect(self.set_sound_path)

        # Sound file format
        label_format = QLabel("Sound Format:")
        self.combobox_format = QComboBox()
        self.combobox_format.setEditable(True)
        self.combobox_format.addItems(("wav", "mp3", "aac"))

        # Global Offset
        label_offset = QLabel("Global Offset:")
        self.spinbox_offset = QDoubleSpinBox()
        self.spinbox_offset.setRange(-9999, 9999)
        self.spinbox_offset.setSingleStep(1)
        self.spinbox_offset.setDecimals(2)
        self.spinbox_offset.setSuffix("m")

        # Max playback duration per sound
        label_max_duration = QLabel("Max Duration:")
        self.spinbox_max_duration = QDoubleSpinBox()
        self.spinbox_max_duration.setRange(0.2, 60)
        self.spinbox_max_duration.setSingleStep(1)
        self.spinbox_max_duration.setDecimals(3)
        self.spinbox_max_duration.setSuffix("s")

        # Max playback queue
        label_max_queue = QLabel("Max Queue:")
        self.spinbox_max_queue = QDoubleSpinBox()
        self.spinbox_max_queue.setRange(1, 50)
        self.spinbox_max_queue.setSingleStep(1)
        self.spinbox_max_queue.setDecimals(0)

        # Sound volumn slider
        self.label_volume = QLabel("Playback Volume: 0%")
        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.valueChanged.connect(self.set_sound_volume)

        # Playback option
        self.checkbox_playinpit = QCheckBox("Enable Playback While in Pit Lane")
        self.checkbox_playinpit.toggled.connect(self.toggle_playinpit_state)

        # Frame layout
        layout_file = QGridLayout()
        layout_file.setAlignment(Qt.AlignTop)
        layout_file.addWidget(self.checkbox_file, 0, 0, 1, 2)
        layout_file.addWidget(self.file_selector, 1, 0)
        layout_file.addWidget(self.button_openfile, 1, 1)

        layout_file.addWidget(label_path, 2, 0, 1, 2)
        layout_file.addWidget(self.path_selector, 3, 0)
        layout_file.addWidget(button_openpath, 3, 1)

        layout_inner = QGridLayout()
        layout_inner.addWidget(label_format, 0, 0)
        layout_inner.addWidget(self.combobox_format, 1, 0)

        layout_inner.addWidget(label_offset, 0, 1)
        layout_inner.addWidget(self.spinbox_offset, 1, 1)

        layout_inner.addWidget(label_max_duration, 2, 0)
        layout_inner.addWidget(self.spinbox_max_duration, 3, 0)

        layout_inner.addWidget(label_max_queue, 2, 1)
        layout_inner.addWidget(self.spinbox_max_queue, 3, 1)

        layout_setting = QVBoxLayout()
        margin = UIScaler.pixel(5)
        layout_setting.setContentsMargins(margin, margin, margin, margin)
        layout_setting.addLayout(layout_file)
        layout_setting.addLayout(layout_inner)
        layout_setting.addStretch(1)
        layout_setting.addWidget(self.label_volume)
        layout_setting.addWidget(self.slider_volume)
        layout_setting.addWidget(self.checkbox_playinpit)

        self.frame_control = QFrame(self)
        self.frame_control.setFrameShape(QFrame.StyledPanel)
        self.frame_control.setLayout(layout_setting)

        # Button
        self.button_apply = QPushButton("Apply")
        self.button_apply.clicked.connect(self.set_playback_setting)

        self.button_toggle = QPushButton("")
        self.button_toggle.setCheckable(True)
        self.button_toggle.clicked.connect(self.toggle_button_state)

        layout_button = QHBoxLayout()
        layout_button.addWidget(self.button_apply)
        layout_button.addStretch(1)
        layout_button.addWidget(self.button_toggle)

        # Layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.frame_control, stretch=1)
        layout_main.addLayout(layout_button)
        margin = UIScaler.pixel(6)
        layout_main.setContentsMargins(margin, margin, margin, margin)
        self.setLayout(layout_main)
        self.refresh()

    def refresh(self):
        """Refresh state"""
        self.mcfg = cfg.user.setting["pace_notes_playback"]
        self.pace_notes_player.mcfg = self.mcfg
        self.toggle_playinpit_state(self.mcfg["enable_playback_while_in_pit"])
        self.toggle_selector_state(self.mcfg["enable_manual_file_selector"])
        self.file_selector.setText(self.mcfg["pace_notes_file_name"])
        self.path_selector.setText(self.mcfg["pace_notes_sound_path"])
        self.combobox_format.setEditText(self.mcfg["pace_notes_sound_format"])
        self.spinbox_offset.setValue(self.mcfg["pace_notes_global_offset"])
        self.spinbox_max_duration.setValue(self.mcfg["pace_notes_sound_max_duration"])
        self.spinbox_max_queue.setValue(self.mcfg["pace_notes_sound_max_queue"])
        self.slider_volume.setValue(self.mcfg["pace_notes_sound_volume"])
        self.set_enable_state(self.mcfg["enable"])

    def set_notes_path(self):
        """Set pace notes file path"""
        filepath = self.mcfg["pace_notes_file_name"]
        filename_full = QFileDialog.getOpenFileName(self, dir=filepath, filter=FileFilter.TPPN)[0]
        if not filename_full:
            return
        self.file_selector.setText(filename_full)
        self.pace_notes_player.reset_playback()
        if self.update_config("pace_notes_file_name", filename_full):
            mctrl.reload("module_notes")  # reload path in module notes

    def set_sound_path(self):
        """Set sounds folder path"""
        filepath = self.mcfg["pace_notes_sound_path"]
        filename_full = QFileDialog.getExistingDirectory(self, dir=filepath)
        if not filename_full:
            return
        filename_full = set_relative_path(filename_full)
        self.path_selector.setText(filename_full)
        self.update_config("pace_notes_sound_path", filename_full)

    def set_playback_setting(self):
        """Set sound playback setting"""
        sound_format = self.combobox_format.currentText()
        self.update_config("pace_notes_sound_format", sound_format)

        global_offset = self.spinbox_offset.value()
        self.update_config("pace_notes_global_offset", global_offset)

        max_duration = self.spinbox_max_duration.value()
        self.update_config("pace_notes_sound_max_duration", max_duration)

        max_queue = int(self.spinbox_max_queue.value())
        self.update_config("pace_notes_sound_max_queue", max_queue)

    def set_sound_volume(self, volume: int):
        """Set sound volume"""
        self.label_volume.setText(f"Playback Volume: {volume}%")
        if self.update_config("pace_notes_sound_volume", volume):
            self.pace_notes_player.set_volume(volume)

    def toggle_selector_state(self, checked: bool):
        """Toggle file selector state"""
        self.checkbox_file.setChecked(checked)
        self.file_selector.setText(self.mcfg["pace_notes_file_name"])
        self.file_selector.setDisabled(not checked)
        self.button_openfile.setDisabled(not checked)

        if self.update_config("enable_manual_file_selector", checked):
            mctrl.reload("module_notes")  # reload file in module notes

    def toggle_playinpit_state(self, checked: bool):
        """Toggle playback in pit state"""
        self.checkbox_playinpit.setChecked(checked)
        self.update_config("enable_playback_while_in_pit", checked)

    def toggle_button_state(self, checked: bool):
        """Toggle button state"""
        self.set_enable_state(checked)
        self.update_config("enable", checked)

    def set_enable_state(self, enabled: bool):
        """Set pace notes enabled state"""
        self.button_toggle.setText("  Playback Enabled  " if enabled else "  Playback Disabled  ")
        self.button_toggle.setChecked(enabled)
        self.button_apply.setDisabled(not enabled)
        self.frame_control.setDisabled(not enabled)
        self.pace_notes_player.set_playback(enabled)
        self.notify_toggle(enabled)

    def update_config(self, key: str, value: int | float | str) -> bool:
        """Update pace note playback setting, save if changed"""
        if self.mcfg[key] == value:
            return False
        self.mcfg[key] = value
        cfg.save()
        return True
