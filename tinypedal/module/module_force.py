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
Force module
"""

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..module_info import ForceInfo, minfo
from ..validator import generator_init
from ._base import DataModule


class Realtime(DataModule):
    """Force data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        gen_force = calc_force(
            output=minfo.force,
            g_accel=max(self.mcfg["gravitational_acceleration"], 0.01),
            max_g_diff=self.mcfg["maximum_average_g_force_difference"],
            max_avg_g_samples=self.mcfg["maximum_average_g_force_samples"],
            max_g_reset_delay=self.mcfg["maximum_g_force_reset_delay"],
            max_avg_g_reset_delay=self.mcfg["maximum_average_g_force_reset_delay"],
            max_braking_rate_reset_delay=self.mcfg["maximum_braking_rate_reset_delay"],
        )

        while not _event_wait(update_interval):
            if realtime_state.active:
                vehicle_resets = realtime_state.resets

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                # Run calculation
                gen_force.send(vehicle_resets)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


@generator_init
def transient_max(reset_delay: float, store_recent: bool = False):
    """Transient max

    Args:
        reset_delay: auto reset delay (seconds).
        store_recent: whether store a recent fallback max value.
    """
    reset_timer = 0.0
    max_value = 0.0
    stored_value = 0.0

    while True:
        data = yield max_value

        # Reset check
        if data is None:
            reset_timer = 0.0
            max_value = 0.0
            stored_value = 0.0
            continue

        value, elapsed = data

        if value > max_value:
            max_value = value
            reset_timer = elapsed
        elif store_recent and max_value > value > stored_value:
            stored_value = value
            reset_timer = elapsed
        elif elapsed - reset_timer > reset_delay:
            max_value = stored_value
            stored_value = 0
            reset_timer = elapsed


@generator_init
def calc_force(
    output: ForceInfo,
    g_accel: float,
    max_g_diff: float,
    max_avg_g_samples: int,
    max_g_reset_delay: float,
    max_avg_g_reset_delay: float,
    max_braking_rate_reset_delay: float,
):
    """Calculate force data"""
    last_reset = None  # reset check

    calc_ema_gforce = calc.ema_filter(max_avg_g_samples, 3)
    calc_max_lgt = transient_max(max_g_reset_delay)
    calc_max_lat = transient_max(max_g_reset_delay)
    calc_max_avg_lat = transient_max(max_avg_g_reset_delay, True)
    calc_max_transient_rate = transient_max(3)
    calc_max_braking_rate = transient_max(max_braking_rate_reset_delay, True)

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            # Delay reset until driving
            if not realtime_state.active:
                continue
            last_reset = reset

            # Reset data
            calc_max_lgt.send(None)
            calc_max_lat.send(None)
            calc_max_avg_lat.send(None)
            calc_max_transient_rate.send(None)
            calc_max_braking_rate.send(None)

            avg_lat_gforce_ema = 0
            max_braking_rate = 0
            delta_braking_rate = 0

        # Read telemetry
        elapsed = api.read.timing.elapsed()
        lat_accel = api.read.vehicle.acceleration_lateral()
        lgt_accel = api.read.vehicle.acceleration_longitudinal()
        dforce_f = api.read.vehicle.downforce_front()
        dforce_r = api.read.vehicle.downforce_rear()
        brake_raw = api.read.inputs.brake_raw()

        # G raw
        lgt_gforce_raw = lgt_accel / g_accel
        lat_gforce_raw = lat_accel / g_accel

        # Max G
        max_lgt_gforce = calc_max_lgt.send((abs(lgt_gforce_raw), elapsed))
        max_lat_gforce = calc_max_lat.send((abs(lat_gforce_raw), elapsed))

        # Max average lateral G
        avg_lat_gforce_ema = calc_ema_gforce(
            avg_lat_gforce_ema,
            min(abs(lat_gforce_raw), avg_lat_gforce_ema + max_g_diff)
        )
        max_avg_lat_gforce = calc_max_avg_lat.send((avg_lat_gforce_ema, elapsed))

        # Downforce
        dforce_ratio = calc.force_ratio(dforce_f, dforce_f + dforce_r)

        # Braking rate (longitudinal G force)
        if brake_raw > 0.02 and elapsed - api.read.vehicle.impact_time() > 2:
            braking_rate = lgt_gforce_raw
        else:
            braking_rate = 0.0

        max_transient_rate = calc_max_transient_rate.send((braking_rate, elapsed))
        temp_max_rate = calc_max_braking_rate.send((max_transient_rate, elapsed))
        if max_transient_rate > 0:
            delta_braking_rate = max_transient_rate - max_braking_rate
        else:  # Set after reset max_transient_rate
            max_braking_rate = temp_max_rate

        # Output force data
        output.lgtGForceRaw = lgt_gforce_raw
        output.latGForceRaw = lat_gforce_raw
        output.maxAvgLatGForce = max_avg_lat_gforce
        output.maxLgtGForce = max_lgt_gforce
        output.maxLatGForce = max_lat_gforce
        output.downForceFront = dforce_f
        output.downForceRear = dforce_r
        output.downForceRatio = dforce_ratio
        output.brakingRate = braking_rate
        output.transientMaxBrakingRate = max_transient_rate
        output.maxBrakingRate = max_braking_rate
        output.deltaBrakingRate = delta_braking_rate
