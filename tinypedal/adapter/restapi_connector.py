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
RestAPI module
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from itertools import chain
from typing import Any

from ..async_request import http_get, set_header_get
from ..const_common import TYPE_JSON
from .rf2_restapi import HttpSetup, ResRawOutput, RestAPIData, select_taskset

logger = logging.getLogger(__name__)
json_decoder = json.JSONDecoder()


class RestAPIInfo:
    """Rest API data output"""

    __slots__ = (
        "_parent_api",
        "_cfg",
        "_task_cancel",
        "_updating",
        "_update_thread",
        "_active_interval",
        "_event",
        "_dataset",
    )

    def __init__(self, parent_api):
        self._parent_api = parent_api
        self._cfg: dict = None

        self._task_cancel = False
        self._updating = False
        self._update_thread = None
        self._active_interval = 0.2
        self._event = threading.Event()

        self._dataset = RestAPIData()

    @property
    def telemetry(self) -> RestAPIData:
        """Rest API telemetry data"""
        return self._dataset

    def __del__(self):
        logger.info("RestAPI: GC: RestAPIInfo")

    def setConnection(self, config: dict):
        """Update connection config"""
        self._cfg = config
        self._active_interval = max(self._cfg["restapi_update_interval"], 100) / 1000

    def start(self):
        """Start update thread"""
        if not self._updating and self._cfg["enable_restapi_access"]:
            self._updating = True
            self._event.clear()
            self._update_thread = threading.Thread(target=self.__update, daemon=True)
            self._update_thread.start()
            logger.info("RestAPI: UPDATING: thread started")

    def stop(self):
        """Stop update thread"""
        if self._updating:
            self._event.set()
            if self._update_thread is not None:
                self._update_thread.join()
            self._updating = False
            logger.info("RestAPI: UPDATING: thread stopped")

    def __update(self):
        """Update Rest API data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = 0.5

        active_task_sim = {}

        while not _event_wait(update_interval):
            if self._parent_api.isActive:

                # Also check task cancel state in case delay
                if not reset or self._task_cancel:
                    reset = True
                    update_interval = self._active_interval
                    self._task_cancel = False
                    self.run_tasks(self._parent_api.identifier, active_task_sim)

            else:
                if reset:
                    reset = False
                    update_interval = 0.5

        # Reset to default on close
        reset_to_default(self._dataset, active_task_sim)

    def run_tasks(self, sim_name: str, active_task_sim: dict):
        """Run tasks"""
        if not sim_name:
            logger.info("RestAPI: game session not found")
            return
        logger.info("RestAPI: session found (%s)", sim_name)
        # Load http connection setting
        sim_http = HttpSetup(
            host=self._cfg["url_host"],
            port=self._cfg.get(f"url_port_{sim_name.lower()}", 0),
            timeout=min(max(self._cfg["connection_timeout"], 0.5), 10),
            retry=min(max(int(self._cfg["connection_retry"]), 0), 10),
            retry_delay=min(max(self._cfg["connection_retry_delay"], 0), 60),
        )
        # Run all tasks while on track, this blocks until tasks cancelled
        logger.info("RestAPI: all tasks started")
        asyncio.run(
            self.task_init(
                self.sort_taskset(sim_http, active_task_sim, select_taskset(sim_name)),
            )
        )
        logger.info("RestAPI: all tasks stopped")
        # Reset when finished
        reset_to_default(self._dataset, active_task_sim)

    def sort_taskset(self, http: HttpSetup, active_task: dict, taskset: tuple):
        """Sort task set into dictionary, key - uri_path, value - output_set"""
        for uri_path, output_set, condition, is_repeat, min_interval in taskset:
            if self._cfg.get(condition, True):
                active_task[uri_path] = output_set
                update_interval = max(min_interval, self._active_interval)
                yield asyncio.create_task(
                    self.fetch(http, uri_path, output_set, is_repeat, update_interval)
                )

    async def task_init(self, *task_generator):
        """Run repeatedly updating task"""
        task_group = tuple(chain(*task_generator))
        # Task control
        await asyncio.create_task(self.task_control(task_group))
        # Start task
        for task in task_group:
            try:
                await task
            except (asyncio.CancelledError, BaseException):
                pass

    async def task_control(self, task_group: tuple[asyncio.Task, ...]):
        """Control task running state"""
        _event_is_set = self._event.is_set
        while not _event_is_set() and self._parent_api.isActive:
            await asyncio.sleep(0.1)  # check every 100ms
        # Set cancel state to exit loop in case failed to cancel
        self._task_cancel = True
        # Cancel all running tasks
        for task in task_group:
            task.cancel()

    async def fetch(
        self, http: HttpSetup, uri_path: str, output_set: tuple[ResRawOutput, ...],
        repeat: bool = False, min_interval: float = 0.01):
        """Fetch data and verify"""
        data_available = await self.update_once(http, uri_path, output_set)
        if not data_available:
            logger.info("RestAPI: MISSING: %s", uri_path)
        elif not repeat:
            logger.info("RestAPI: ACTIVE: %s (one time)", uri_path)
        else:
            logger.info("RestAPI: ACTIVE: %s (%sms)", uri_path, int(min_interval * 1000))
            await self.update_repeat(http, uri_path, output_set, min_interval)

    async def update_once(
        self, http: HttpSetup, uri_path: str, output_set: tuple[ResRawOutput, ...]) -> bool:
        """Update once and verify"""
        request_header = set_header_get(uri_path, http.host)
        data_available = False
        total_retry = retry = http.retry
        while not self._task_cancel and retry >= 0:
            resource_output = await get_resource(request_header, http)
            # Verify & retry
            if not isinstance(resource_output, TYPE_JSON):
                logger.info("RestAPI: %s: %s (%s/%s retries left)",
                    resource_output, uri_path, retry, total_retry)
                retry -= 1
                if retry < 0:
                    data_available = False
                    break
                await asyncio.sleep(http.retry_delay)
                continue
            # Output
            for res in output_set:
                if res.update(self._dataset, resource_output):
                    data_available = True
            break
        return data_available

    async def update_repeat(
        self, http: HttpSetup, uri_path: str, output_set: tuple[ResRawOutput, ...], min_interval: float):
        """Update repeat"""
        request_header = set_header_get(uri_path, http.host)
        interval = min_interval
        last_hash = new_hash = -1
        while not self._task_cancel:  # use task control to cancel & exit loop
            new_hash = await output_resource(self._dataset, request_header, http, output_set, last_hash)
            if last_hash != new_hash:
                last_hash = new_hash
                interval = min_interval
            elif interval < 5:  # increase update interval while no new data
                interval += interval / 2
                if interval > 5:
                    interval = 5
            await asyncio.sleep(interval)


def reset_to_default(dataset: RestAPIData, active_task: dict[str, tuple[ResRawOutput, ...]]):
    """Reset active task data to default"""
    if active_task:
        for uri_path, output_set in active_task.items():
            for res in output_set:
                res.reset(dataset)
            logger.info("RestAPI: RESET: %s", uri_path)
        active_task.clear()


async def get_resource(request: bytes, http: HttpSetup) -> Any | str:
    """Get resource from REST API"""
    try:
        async with http_get(request, http.host, http.port, http.timeout) as raw_bytes:
            return json_decoder.decode(raw_bytes.decode())
    except (AttributeError, TypeError, IndexError, KeyError, ValueError,
            OSError, TimeoutError, BaseException):
        return "INVALID"


async def output_resource(
    dataset: RestAPIData, request: bytes, http: HttpSetup, output_set: tuple[ResRawOutput, ...], last_hash: int) -> int:
    """Get resource from REST API and output data, skip unnecessary checking"""
    try:
        async with http_get(request, http.host, http.port, http.timeout) as raw_bytes:
            new_hash = hash(raw_bytes)
            if last_hash != new_hash:
                resource_output = json_decoder.decode(raw_bytes.decode())
                for res in output_set:
                    res.update(dataset, resource_output)
            return new_hash
    except (AttributeError, TypeError, IndexError, KeyError, ValueError,
            OSError, TimeoutError, BaseException):
        return last_hash
