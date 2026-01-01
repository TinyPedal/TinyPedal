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
Weather Widget
"""

from ..api_control import api
from ..const_common import TEXT_TREND_SIGN
from ..module_info import minfo
from ..units import set_symbol_temperature, set_unit_temperature
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        prefix_wetness_just = max(len(self.wcfg["prefix_dry"]), len(self.wcfg["prefix_wet"]))
        decimals = min(max(self.wcfg["decimal_places_temperature"], 0), 6)

        self.prefix_rain = self.wcfg["prefix_rain"]
        self.prefix_dry = self.wcfg["prefix_dry"].ljust(prefix_wetness_just)
        self.prefix_wet = self.wcfg["prefix_wet"].ljust(prefix_wetness_just)
        self.temp_cut = 2 + (self.cfg.units["temperature_unit"] == "Fahrenheit") + (decimals != 0) + decimals
        self.temp_digits = f"0{self.temp_cut + round(0.1 + decimals * 0.1, decimals)}f"

        self.rubber_median_laps = max(int(self.wcfg["rubber_median_laps"]), 100)
        self.rubber_time_scale = (
            self.wcfg["rubber_time_scale_practice"],  # testday
            self.wcfg["rubber_time_scale_practice"],  # practice
            self.wcfg["rubber_time_scale_qualifying"],  # qualifying
            self.wcfg["rubber_time_scale_race"],  # warmup
            self.wcfg["rubber_time_scale_race"],  # race
        )
        self.rubber_starting = (
            self.wcfg["starting_rubber_practice"],  # testday
            self.wcfg["starting_rubber_practice"],  # practice
            self.wcfg["starting_rubber_qualifying"],  # qualifying
            self.wcfg["starting_rubber_race"],  # warmup
            self.wcfg["starting_rubber_race"],  # race
        )

        # Config units
        self.unit_temp = set_unit_temperature(self.cfg.units["temperature_unit"])
        self.symbol_temp = set_symbol_temperature(self.cfg.units["temperature_unit"])

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Track temperature
        if self.wcfg["show_temperature"]:
            layout_temp = self.set_grid_layout()
            track_temp = f"{self.unit_temp(0):{self.temp_digits}}"[:self.temp_cut]
            air_temp = f"{self.unit_temp(0):{self.temp_digits}}"[:self.temp_cut]
            text_temp = f"{track_temp}({air_temp}){self.symbol_temp}"
            bar_style_temp = self.set_qss(
                fg_color=self.wcfg["font_color_temperature"],
                bg_color=self.wcfg["bkg_color_temperature"]
            )
            self.bar_temp = self.set_qlabel(
                text=text_temp,
                style=bar_style_temp,
                width=font_m.width * len(text_temp) + bar_padx,
                last=0,
            )
            layout_temp.addWidget(self.bar_temp, 0, 0)

            self.bar_style_temp_trend = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_constant"],
                    bg_color=self.wcfg["bkg_color_temperature"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_increasing"],
                    bg_color=self.wcfg["bkg_color_temperature"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_decreasing"],
                    bg_color=self.wcfg["bkg_color_temperature"]),
            )
            self.bar_temp_trend = self.set_qlabel(
                text=TEXT_TREND_SIGN[0],
                style=self.bar_style_temp_trend[0],
                width=font_m.width + bar_padx,
                last=0,
            )
            layout_temp.addWidget(self.bar_temp_trend, 0, 1)
            self.set_primary_orient(
                target=layout_temp,
                column=self.wcfg["column_index_temperature"],
                option=None,
                default=1,
            )

        # Rain precipitation
        if self.wcfg["show_rain"]:
            layout_rain = self.set_grid_layout()
            text_rain = f"{self.prefix_rain}  0%"
            bar_style_rain = self.set_qss(
                fg_color=self.wcfg["font_color_rain"],
                bg_color=self.wcfg["bkg_color_rain"]
            )
            self.bar_rain = self.set_qlabel(
                text=text_rain,
                style=bar_style_rain,
                width=font_m.width * len(text_rain) + bar_padx,
                last=0,
            )
            layout_rain.addWidget(self.bar_rain, 0, 0)

            self.bar_style_raininess_trend = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_constant"],
                    bg_color=self.wcfg["bkg_color_rain"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_increasing"],
                    bg_color=self.wcfg["bkg_color_rain"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_decreasing"],
                    bg_color=self.wcfg["bkg_color_rain"]),
            )
            self.bar_raininess_trend = self.set_qlabel(
                text=TEXT_TREND_SIGN[0],
                style=self.bar_style_raininess_trend[0],
                width=font_m.width + bar_padx,
                last=0,
            )
            layout_rain.addWidget(self.bar_raininess_trend, 0, 1)
            self.set_primary_orient(
                target=layout_rain,
                column=self.wcfg["column_index_rain"],
                option=None,
                default=1,
            )

        # Surface wetness
        if self.wcfg["show_wetness"]:
            layout_wetness = self.set_grid_layout()
            text_wetness = f"{self.prefix_dry}  0%"
            bar_style_wetness = self.set_qss(
                fg_color=self.wcfg["font_color_wetness"],
                bg_color=self.wcfg["bkg_color_wetness"]
            )
            self.bar_wetness = self.set_qlabel(
                text=text_wetness,
                style=bar_style_wetness,
                width=font_m.width * len(text_wetness) + bar_padx,
                last=0,
            )
            layout_wetness.addWidget(self.bar_wetness, 0, 0)

            self.bar_style_wetness_trend = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_constant"],
                    bg_color=self.wcfg["bkg_color_wetness"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_increasing"],
                    bg_color=self.wcfg["bkg_color_wetness"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_trend_decreasing"],
                    bg_color=self.wcfg["bkg_color_wetness"]),
            )
            self.bar_wetness_trend = self.set_qlabel(
                text=TEXT_TREND_SIGN[0],
                style=self.bar_style_wetness_trend[0],
                width=font_m.width + bar_padx,
                last=0,
            )
            layout_wetness.addWidget(self.bar_wetness_trend, 0, 1)
            self.set_primary_orient(
                target=layout_wetness,
                column=self.wcfg["column_index_wetness"],
                option=None,
                default=1,
            )

        # Last data
        self.temp_trend = TrendTimer(self.wcfg["temperature_trend_interval"])
        self.rain_trend = TrendTimer(self.wcfg["raininess_trend_interval"])
        self.wet_trend = TrendTimer(self.wcfg["wetness_trend_interval"])

    def timerEvent(self, event):
        """Update when vehicle on track"""
        lap_etime = api.read.timing.elapsed()

        # Track temperature
        if self.wcfg["show_temperature"]:
            temp_track = api.read.session.track_temperature()
            temp_air = api.read.session.ambient_temperature()
            temperature = temp_track + temp_air
            # Temperature
            self.update_temperature(self.bar_temp, temperature, temp_track, temp_air)
            # Temperature trend
            temp_trend = self.temp_trend.update(round(temperature, 1), lap_etime)
            self.update_temperature_trend(self.bar_temp_trend, temp_trend)

        # Rain precipitation
        if self.wcfg["show_rain"]:
            raininess = round(api.read.session.raininess(), 2)
            # Rain percentage
            self.update_raininess(self.bar_rain, raininess)
            # Rain trend
            rain_trend = self.rain_trend.update(raininess, lap_etime)
            self.update_raininess_trend(self.bar_raininess_trend, rain_trend)

        # Surface wetness
        if self.wcfg["show_wetness"]:
            wet_min, wet_max, wet_avg = api.read.session.wetness()
            # Wetness percentage
            if wet_avg >= 0.01 or not self.wcfg["show_rubber_coverage_while_dry"]:
                self.update_wetness(self.bar_wetness, wet_avg)
            # Rubber coverage percentage
            else:
                session_type = api.read.session.session_type()
                rubber_scale = self.rubber_time_scale[session_type]
                laps_session = rubber_to_laps(self.rubber_starting[session_type], self.rubber_median_laps)
                if rubber_scale > 0:  # time-scaled coverage
                    laps_session += (minfo.vehicles.completedSessionLaps * rubber_scale)
                self.update_rubber(self.bar_wetness, laps_session)
            # Wet trend
            wetness = wet_min + wet_max + wet_avg
            wet_trend = self.wet_trend.update(wetness, lap_etime)
            self.update_wetness_trend(self.bar_wetness_trend, wet_trend)

    # GUI update methods
    def update_temperature(self, target, data, track, air):
        """Track & ambient temperature"""
        if target.last != data:
            target.last = data
            track_temp = f"{self.unit_temp(track):{self.temp_digits}}"[:self.temp_cut]
            air_temp = f"{self.unit_temp(air):{self.temp_digits}}"[:self.temp_cut]
            target.setText(f"{track_temp}({air_temp}){self.symbol_temp}")

    def update_temperature_trend(self, target, data):
        """Temperature trend"""
        if target.last != data:
            target.last = data
            target.setText(TEXT_TREND_SIGN[data])
            target.updateStyle(self.bar_style_temp_trend[data])

    def update_raininess(self, target, data):
        """Rain percentage"""
        if target.last != data:
            target.last = data
            percent_rain = f"{data: >3.0%}"[:3]
            target.setText(f"{self.prefix_rain} {percent_rain}")

    def update_raininess_trend(self, target, data):
        """Raininess trend"""
        if target.last != data:
            target.last = data
            target.setText(TEXT_TREND_SIGN[data])
            target.updateStyle(self.bar_style_raininess_trend[data])

    def update_wetness(self, target, data):
        """Surface wetness percentage"""
        if target.last != data:
            target.last = data
            percent_wet = f"{data: >3.0%}"[:3]
            target.setText(f"{self.prefix_wet} {percent_wet}")

    def update_rubber(self, target, data):
        """Surface rubber coverage percentage"""
        if target.last != data:
            target.last = data
            percent_rubber = f"{laps_to_rubber(data, self.rubber_median_laps): >3.0%}"[:3]
            target.setText(f"{self.prefix_dry} {percent_rubber}")

    def update_wetness_trend(self, target, data):
        """Surface wetness trend"""
        if target.last != data:
            target.last = data
            target.setText(TEXT_TREND_SIGN[data])
            target.updateStyle(self.bar_style_wetness_trend[data])


def laps_to_rubber(value: float, median_laps: int = 2000) -> float:
    """Convert laps to rubber coverage (percent)"""
    max_laps = median_laps * 2
    if value > max_laps:
        return 1.0
    if value > median_laps:
        return 0.75 + (value - median_laps) / median_laps / 4
    if value > 0:
        return value * 0.75 / median_laps
    return 0.0


def rubber_to_laps(value: float, median_laps: int = 2000) -> float:
    """Convert rubber coverage (percent) to laps"""
    max_laps = median_laps * 2
    if value >= 1:
        return max_laps
    if value > 0.75:
        return median_laps + (value - 0.75) * median_laps * 4
    if value > 0:
        return value * median_laps / 0.75
    return 0


class TrendTimer:
    """Trend timer"""

    __slots__ = (
        "_trend_interval",
        "_last_reading",
        "_trend",
        "_timer",
    )

    def __init__(self, trend_interval: float) -> None:
        """
        Args:
            trend_interval: trend reset interval (seconds).
        """
        self._trend_interval = trend_interval
        self._last_reading = 0.0
        self._trend = 0
        self._timer = 0.0

    def update(self, reading: float, elapsed_time: float) -> int:
        """Update trend

        Args:
            reading: value.
            elapsed_time: current lap elapsed time.

        Returns:
            Trend, 0 = constant, 1 = increasing, -1 = decreasing.
        """
        if self._last_reading < reading:
            self._timer = elapsed_time
            self._trend = 1  # increased
        elif self._last_reading > reading:
            self._timer = elapsed_time
            self._trend = -1  # decreased
        elif elapsed_time - self._timer > self._trend_interval:
            self._timer = elapsed_time
            self._trend = 0  # no change
        self._last_reading = reading

        if self._timer > elapsed_time:
            self._timer = elapsed_time
        return self._trend
