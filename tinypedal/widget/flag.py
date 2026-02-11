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
Flag Widget
"""

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import MAX_SECONDS
from ..module_info import minfo
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = font_m.width * 7 + bar_padx

        # Config units
        self.unit_fuel = units.set_unit_fuel(self.cfg.units["fuel_unit"])
        self.unit_dist = units.set_unit_distance(self.cfg.units["distance_unit"])
        self.symbol_dist = units.set_symbol_distance(self.cfg.units["distance_unit"])

        # Pit status
        if self.wcfg["show_pit_timer"]:
            self.bar_style_pit_timer = (
                (
                    self.wcfg["font_color_pit_timer"],
                    self.wcfg["bkg_color_pit_timer"],
                ),
                (
                    self.wcfg["font_color_pit_timer_stopped"],
                    self.wcfg["bkg_color_pit_timer_stopped"],
                ),
                (
                    self.wcfg["font_color_pit_closed"],
                    self.wcfg["bkg_color_pit_closed"],
                ),
            )
            self.bar_pit_timer = self.set_rawtext(
                text="PITST0P",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.bar_style_pit_timer[0][0],
                bg_color=self.bar_style_pit_timer[0][1],
            )
            self.set_primary_orient(
                target=self.bar_pit_timer,
                column=self.wcfg["column_index_pit_timer"],
            )

        # Low fuel warning
        if self.wcfg["show_low_fuel"]:
            self.bar_lowfuel = self.set_rawtext(
                text="LOWFUEL",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_low_fuel"],
                bg_color=self.wcfg["bkg_color_low_fuel"],
            )
            self.set_primary_orient(
                target=self.bar_lowfuel,
                column=self.wcfg["column_index_low_fuel"],
            )

        # Speed limiter
        if self.wcfg["show_speed_limiter"]:
            self.bar_limiter = self.set_rawtext(
                text=self.wcfg["speed_limiter_text"],
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_speed_limiter"],
                bg_color=self.wcfg["bkg_color_speed_limiter"],
            )
            self.set_primary_orient(
                target=self.bar_limiter,
                column=self.wcfg["column_index_speed_limiter"],
            )

        # Yellow flag
        if self.wcfg["show_yellow_flag"]:
            self.bar_yellowflag = self.set_rawtext(
                text="YELLOW",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_yellow_flag"],
                bg_color=self.wcfg["bkg_color_yellow_flag"],
            )
            self.set_primary_orient(
                target=self.bar_yellowflag,
                column=self.wcfg["column_index_yellow_flag"],
            )

        # Blue flag
        if self.wcfg["show_blue_flag"]:
            self.bar_blueflag = self.set_rawtext(
                text="BLUE",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_blue_flag"],
                bg_color=self.wcfg["bkg_color_blue_flag"],
            )
            self.set_primary_orient(
                target=self.bar_blueflag,
                column=self.wcfg["column_index_blue_flag"],
            )

        # Start lights
        if self.wcfg["show_startlights"]:
            self.bar_style_startlights = (
                self.wcfg["bkg_color_red_lights"],
                self.wcfg["bkg_color_green_flag"],
            )
            self.bar_startlights = self.set_rawtext(
                text="SLIGHTS",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_startlights"],
                bg_color=self.bar_style_startlights[0],
            )
            self.set_primary_orient(
                target=self.bar_startlights,
                column=self.wcfg["column_index_startlights"],
            )

        # Incoming traffic
        if self.wcfg["show_traffic"]:
            self.bar_traffic = self.set_rawtext(
                text="TRAFFIC",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_traffic"],
                bg_color=self.wcfg["bkg_color_traffic"],
            )
            self.set_primary_orient(
                target=self.bar_traffic,
                column=self.wcfg["column_index_traffic"],
            )

        # Pit request
        if self.wcfg["show_pit_request"]:
            self.bar_pit_request = self.set_rawtext(
                text="PIT REQ",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_pit_request"],
                bg_color=self.wcfg["bkg_color_pit_request"],
            )
            self.set_primary_orient(
                target=self.bar_pit_request,
                column=self.wcfg["column_index_pit_request"],
            )

        # Finish state
        if self.wcfg["show_finish_state"]:
            self.bar_style_finish_state = (
                (
                    self.wcfg["font_color_finish"],
                    self.wcfg["bkg_color_finish"],
                ),
                (
                    self.wcfg["font_color_disqualify"],
                    self.wcfg["bkg_color_disqualify"],
                ),
            )
            self.bar_finish_state = self.set_rawtext(
                text="FINISH",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.bar_style_finish_state[0][0],
                bg_color=self.bar_style_finish_state[0][1],
            )
            self.set_primary_orient(
                target=self.bar_finish_state,
                column=self.wcfg["column_index_finish_state"],
            )

        # Last data
        self.pit_timer = PitTimer(self.wcfg["pit_time_highlight_duration"])
        self.green_timer = GreenFlagTimer(self.wcfg["green_flag_duration"])
        self.blue_timer = BlueFlagTimer(self.wcfg["show_blue_flag_for_race_only"])
        self.traffic_timer = TrafficTimer(
            self.wcfg["traffic_maximum_time_gap"],
            self.wcfg["traffic_pitout_duration"],
            self.wcfg["traffic_low_speed_threshold"],
        )

    def post_update(self):
        self.pit_timer.reset()
        self.blue_timer.reset()
        self.traffic_timer.reset()
        self.green_timer.reset()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Read state data
        lap_etime = api.read.timing.elapsed()
        in_pits = api.read.vehicle.in_pits()
        in_race = api.read.session.in_race()

        # Pit timer
        if self.wcfg["show_pit_timer"]:
            if in_pits and api.read.vehicle.in_garage():
                pitting_state = MAX_SECONDS
            else:
                pitting_state = self.pit_timer.update(in_pits, lap_etime)
            self.update_pit_timer(self.bar_pit_timer, pitting_state)

        # Low fuel update
        if self.wcfg["show_low_fuel"]:
            fuel_usage = self.is_lowfuel(in_race)
            self.update_lowfuel(self.bar_lowfuel, fuel_usage)

        # Pit limiter
        if self.wcfg["show_speed_limiter"]:
            limiter_state = api.read.switch.speed_limiter()
            self.update_limiter(self.bar_limiter, limiter_state)

        # Blue flag
        if self.wcfg["show_blue_flag"]:
            blue_state = self.blue_timer.update(in_race, lap_etime)
            self.update_blueflag(self.bar_blueflag, blue_state)

        # Yellow flag
        if self.wcfg["show_yellow_flag"]:
            yellow_state = self.yellow_flag_state(in_race)
            self.update_yellowflag(self.bar_yellowflag, yellow_state)

        # Start lights
        if self.wcfg["show_startlights"]:
            green_state = self.green_timer.update(lap_etime)
            self.update_startlights(self.bar_startlights, green_state)

        # Incoming traffic
        if self.wcfg["show_traffic"]:
            traffic = self.traffic_timer.update(in_pits, lap_etime)
            self.update_traffic(self.bar_traffic, traffic)

        # Pit request
        if self.wcfg["show_pit_request"]:
            pit_request = self.pit_in_countdown()
            self.update_pit_request(self.bar_pit_request, pit_request)

        # Finish state
        if self.wcfg["show_finish_state"]:
            finish_state = api.read.vehicle.finish_state()
            self.update_finish_state(self.bar_finish_state, finish_state)

    # GUI update methods
    def update_pit_timer(self, target, data):
        """Pit timer"""
        if target.last != data:
            target.last = data
            if data != MAX_SECONDS:
                if data < 0:  # finished pits
                    color_index = 1
                    state = f"F{-data: >6.2f}"[:7]
                elif api.read.session.pit_open():
                    color_index = 0
                    state = f"P{data: >6.2f}"[:7]
                else:  # pit closed
                    color_index = 2
                    state = self.wcfg["pit_closed_text"]
                target.text = state
                target.fg, target.bg = self.bar_style_pit_timer[color_index]
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    def update_lowfuel(self, target, data):
        """Low fuel warning"""
        if target.last != data:
            target.last = data
            if data != "":
                target.text = data
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    def update_limiter(self, target, data):
        """Speed limiter"""
        if target.last != data:
            target.last = data
            target.setHidden(not data)

    def update_blueflag(self, target, data):
        """Blue flag"""
        if target.last != data:
            target.last = data
            if data != MAX_SECONDS:
                target.text = f"BLUE{data:3.0f}"[:7]
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    def update_yellowflag(self, target, data):
        """Yellow flag"""
        if target.last != data:
            target.last = data
            if data != MAX_SECONDS:
                text = f"{self.unit_dist(data):+.0f}{self.symbol_dist}"
                target.text = f"Y{text: >6}"[:7]
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    def update_startlights(self, target, data):
        """Start lights"""
        if target.last != data:
            target.last = data
            if data > 0:
                target.text = f"{self.wcfg['red_lights_text'][:6]: <6}{data}"
                target.bg = self.bar_style_startlights[0]
                target.update()
                hidden = False
            elif data == 0:
                target.text = self.wcfg["green_flag_text"]
                target.bg = self.bar_style_startlights[1]
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    def update_traffic(self, target, data):
        """Incoming traffic"""
        if target.last != data:
            target.last = data
            if data != MAX_SECONDS:
                target.text = f"≥{data: >5.1f}s"[:7]
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    def update_pit_request(self, target, data):
        """Pit request"""
        if target.last != data:
            target.last = data
            if data != "":
                target.text = data
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    def update_finish_state(self, target, data):
        """Finish state"""
        if target.last != data:
            target.last = data
            if data == 1:
                target.text = self.wcfg["finish_text"]
                target.fg, target.bg = self.bar_style_finish_state[0]
                target.update()
                hidden = False
            elif data == 3:
                target.text = self.wcfg["disqualify_text"]
                target.fg, target.bg = self.bar_style_finish_state[1]
                target.update()
                hidden = False
            else:
                hidden = True

            if target.state != hidden:
                target.state = hidden
                target.setHidden(hidden)

    # Additional methods
    def is_lowfuel(self, in_race):
        """Is low fuel"""
        if self.wcfg["show_low_fuel_for_race_only"] and not in_race:
            return ""

        if api.read.vehicle.max_virtual_energy() and minfo.energy.estimatedLaps < minfo.fuel.estimatedLaps:
            prefix = "LE"
            amount_curr = minfo.energy.amountCurrent
            est_laps = minfo.energy.estimatedLaps
        else:
            prefix = "LF"
            amount_curr = minfo.fuel.amountCurrent
            est_laps = minfo.fuel.estimatedLaps

        if (amount_curr > self.wcfg["low_fuel_volume_threshold"] or
            est_laps > self.wcfg["low_fuel_lap_threshold"]):
            return ""  # not low fuel

        if prefix == "LF":
            amount_curr = self.unit_fuel(amount_curr)
        return f"{prefix}{amount_curr: >5.2f}"[:7]

    def pit_in_countdown(self) -> str:
        """Pit in countdown (laps)"""
        if not api.read.vehicle.pit_request():
            return ""

        if api.read.vehicle.max_virtual_energy():
            est_laps = min(minfo.fuel.estimatedLaps, minfo.energy.estimatedLaps)
        else:
            est_laps = minfo.fuel.estimatedLaps
        cd_laps = calc.pit_in_countdown_laps(est_laps, api.read.lap.progress())

        safe_laps = f"{cd_laps:.2f}"[:3].strip(".")
        est_laps = f"{est_laps:.2f}"[:3].strip(".")
        return f"{safe_laps: <3}≤{est_laps: >3}"

    def yellow_flag_state(self, in_race: bool) -> float:
        """Yellow flag state"""
        if not self.wcfg["show_yellow_flag_for_race_only"] or in_race:
            if api.read.session.yellow_flag():
                yellow_ahead = minfo.vehicles.nearestYellowAhead
                if yellow_ahead <= self.wcfg["yellow_flag_maximum_range_ahead"]:
                    return yellow_ahead
                yellow_behind = minfo.vehicles.nearestYellowBehind
                if yellow_behind >= -self.wcfg["yellow_flag_maximum_range_behind"]:
                    return yellow_behind
        return MAX_SECONDS


class GreenFlagTimer:
    """Green flag timer"""

    __slots__ = (
        "_last_lap_stime",
        "_green_flag_duration",
    )

    def __init__(self, green_flag_duration: bool):
        self._last_lap_stime = -1
        self._green_flag_duration = green_flag_duration

    def update(self, elapsed_time: float) -> int:
        """Check start lights and green flag state"""
        if api.read.session.in_countdown():
            self._last_lap_stime = api.read.timing.start()

        if self._last_lap_stime == -1:
            return -1  # bypass checking after green flag

        start_timer = elapsed_time - self._last_lap_stime
        if start_timer > self._green_flag_duration:
            self._last_lap_stime = -1
            return -1 # disable green flag
        if start_timer < 0:
            return api.read.session.start_lights()  # enable red lights
        return 0  # enable green flag

    def reset(self):
        """Reset"""
        self._last_lap_stime = -1


class TrafficTimer:
    """Traffic timer"""

    __slots__ = (
        "_timer_start",
        "_last_in_pits",
        "_max_time_gap",
        "_pitout_duration",
        "_low_speed_threshold",
    )

    def __init__(self, max_time_gap: bool, pitout_duration: float, low_speed_threshold: float):
        self._timer_start = 0.0
        self._last_in_pits = 0
        self._max_time_gap = max_time_gap
        self._pitout_duration = pitout_duration
        self._low_speed_threshold = low_speed_threshold

    def update(self, in_pits: bool, elapsed_time: float) -> float:
        """Check incoming traffic and time gap"""
        if self._last_in_pits > in_pits:
            self._timer_start = elapsed_time
        self._last_in_pits = in_pits

        if self._timer_start and elapsed_time - self._timer_start > self._pitout_duration:
            self._timer_start = 0

        traffic_time = minfo.vehicles.nearestTraffic
        if traffic_time < self._max_time_gap:
            if (api.read.vehicle.speed() < self._low_speed_threshold > 0
                or in_pits or self._timer_start):
                return traffic_time
        return MAX_SECONDS

    def reset(self):
        """Reset"""
        self._timer_start = 0
        self._last_in_pits = 0


class BlueFlagTimer:
    """Blue flag timer"""

    __slots__ = (
        "_timer_start",
        "_race_only",
    )

    def __init__(self, race_only: bool):
        self._timer_start = 0.0
        self._race_only = race_only

    def update(self, in_race: bool, elapsed_time: float) -> float:
        """Check blue flag state"""
        if not self._race_only or in_race:
            if api.read.session.blue_flag():
                if not self._timer_start:
                    self._timer_start = elapsed_time
                return elapsed_time - self._timer_start
            self._timer_start = 0
        return MAX_SECONDS

    def reset(self):
        """Reset"""
        self._timer_start = 0


class PitTimer:
    """Pit timer"""

    __slots__ = (
        "_timer_start",
        "_last_in_pits",
        "_last_pit_time",
        "_max_duration",
    )

    def __init__(self, highlight_duration: float):
        self._timer_start = 0.0
        self._last_in_pits = 0
        self._last_pit_time = 0.0
        self._max_duration = highlight_duration

    def update(self, in_pits: bool, elapsed_time: float) -> float:
        """Check pit state"""
        if self._last_in_pits < in_pits:
            self._timer_start = elapsed_time
        self._last_in_pits = in_pits

        if not self._timer_start:
            return MAX_SECONDS

        pit_timer = elapsed_time - self._timer_start
        if in_pits:
            self._last_pit_time = pit_timer
        elif pit_timer - self._last_pit_time <= self._max_duration:
            pit_timer = -self._last_pit_time  # set negative for highlighting
        else:
            self._timer_start = 0  # stop timer
            pit_timer = MAX_SECONDS
        return pit_timer

    def reset(self):
        """Reset"""
        self._timer_start = 0
        self._last_in_pits = 0
        self._last_pit_time = 0
