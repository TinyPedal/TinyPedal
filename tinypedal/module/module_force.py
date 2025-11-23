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
Force module
"""

from functools import partial

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..module_info import minfo
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

        output = minfo.force
        g_accel = max(self.mcfg["gravitational_acceleration"], 0.01)
        max_g_diff = self.mcfg["max_average_g_force_difference"]
        calc_ema_gforce = partial(
            calc.exp_mov_avg,
            calc.ema_factor(min(max(self.mcfg["max_average_g_force_samples"], 3), 1000))
        )

        calc_max_lgt = TransientMax(self.mcfg["max_g_force_reset_delay"])
        calc_max_lat = TransientMax(self.mcfg["max_g_force_reset_delay"])
        calc_max_avg_lat = TransientMax(self.mcfg["max_average_g_force_reset_delay"], True)
        calc_transient_rate = TransientMax(3)
        calc_max_braking_rate = TransientMax(self.mcfg["max_braking_rate_reset_delay"], True)

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    calc_max_lgt.reset()
                    calc_max_lat.reset()
                    calc_max_avg_lat.reset()
                    calc_transient_rate.reset()
                    calc_max_braking_rate.reset()

                    avg_lat_gforce_ema = 0
                    max_braking_rate = 0
                    delta_braking_rate = 0

                # Read telemetry
                lap_etime = api.read.timing.elapsed()
                lat_accel = api.read.vehicle.accel_lateral()
                lgt_accel = api.read.vehicle.accel_longitudinal()
                dforce_f = api.read.vehicle.downforce_front()
                dforce_r = api.read.vehicle.downforce_rear()
                brake_raw = api.read.inputs.brake_raw()
                impact_time = api.read.vehicle.impact_time()

                # G raw
                lgt_gforce_raw = lgt_accel / g_accel
                lat_gforce_raw = lat_accel / g_accel

                # Max G
                max_lgt_gforce = calc_max_lgt.update(abs(lgt_gforce_raw), lap_etime)
                max_lat_gforce = calc_max_lat.update(abs(lat_gforce_raw), lap_etime)

                # Max average lateral G
                avg_lat_gforce_ema = calc_ema_gforce(
                    avg_lat_gforce_ema,
                    min(abs(lat_gforce_raw), avg_lat_gforce_ema + max_g_diff)
                )
                max_avg_lat_gforce = calc_max_avg_lat.update(avg_lat_gforce_ema, lap_etime)

                # Downforce
                dforce_ratio = calc.force_ratio(dforce_f, dforce_f + dforce_r)

                # Braking rate
                braking_rate = calc.braking_rate(lgt_gforce_raw, brake_raw > 0.02, lap_etime - impact_time > 2)
                max_transient_rate = calc_transient_rate.update(braking_rate, lap_etime)
                temp_max_rate = calc_max_braking_rate.update(max_transient_rate, lap_etime)
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

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


class TransientMax:
    """Transient max"""

    __slots__ = (
        "_reset_delay",
        "_store_recent",
        "_reset_timer",
        "_max_value",
        "_stored_value",
    )

    def __init__(self, reset_delay: float, store_recent: bool = False):
        """
        Args:
            reset_delay: auto reset delay (seconds).
            store_recent: whether store a recent fallback max value.
        """
        self._reset_delay = reset_delay
        self._store_recent = store_recent
        self._reset_timer = 0.0
        self._max_value = 0.0
        self._stored_value = 0.0

    def update(self, value: float, elapsed_time: float) -> float:
        """Record transient max value, reset periodically

        Args:
            value: current value.
            elapsed_time: elapsed time (seconds).

        Returns:
            Max value.
        """
        if value > self._max_value:
            self._max_value = value
            self._reset_timer = elapsed_time
        elif self._store_recent and self._max_value > value > self._stored_value:
            self._stored_value = value
            self._reset_timer = elapsed_time
        elif elapsed_time - self._reset_timer > self._reset_delay:
            self._max_value = self._stored_value
            self._stored_value = 0
            self._reset_timer = elapsed_time
        return self._max_value

    def reset(self):
        """Reset"""
        self._reset_timer = 0.0
        self._max_value = 0.0
        self._stored_value = 0.0
