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
ACC UDP API connector
"""

from __future__ import annotations

import logging
import secrets
import socket
import threading
from time import monotonic

from .. import realtime_state
from ..constant import APP
from .acc_sharedmemory import ACCConstants, acc_udp

logger = logging.getLogger(__name__)


class UDPAPIConnector:
    """UDP API connector"""

    __slots__ = (
        "_cfg",
        "_data_buffer",
        "_event",
        "_update_thread",
        "_updating",
        "output",
    )

    def __init__(self):
        self._cfg: dict = None
        self._updating = False
        self._update_thread = None
        self._event = threading.Event()
        self._data_buffer = bytearray(acc_udp.UDPBroadcastOutput.size())
        self.output = acc_udp.UDPBroadcastOutput.from_buffer(self._data_buffer)

    def __del__(self):
        logger.info("UDP: GC: UDPAPIConnector")

    def reset_output(self):
        """Reset data output"""
        self._data_buffer[:] = bytes(acc_udp.UDPBroadcastOutput.size())
        logger.info("UDP: RESET: UDPBroadcastOutput")

    def setConnection(self, config: dict):
        """Update connection config"""
        self._cfg = config

    def start(self):
        """Start update thread"""
        if not self._updating and self._cfg["enable_upd_api_access"]:
            self._updating = True
            self._event.clear()
            self._update_thread = threading.Thread(target=self.__update, daemon=True)
            self._update_thread.start()
            logger.info("UDP: UPDATING: thread started")

    def stop(self):
        """Stop update thread"""
        if self._updating:
            self._event.set()
            if self._update_thread is not None:
                self._update_thread.join()
            self.reset_output()
            self._updating = False
            logger.info("UDP: UPDATING: thread stopped")

    def __update(self):
        """Update UDP API data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = 0.5

        udp_host = self._cfg["url_host"]
        udp_port = self._cfg["url_port"]
        upd_update_interval = max(self._cfg["upd_api_update_interval"], 200)
        connection_timeout = max(self._cfg["connection_timeout"], 1)
        total_retry = max(int(self._cfg["connection_retry"]), 0)
        connection_retry_delay = min(max(self._cfg["connection_retry_delay"], 0.5), 60)
        udp_output = self.output

        connection_message = acc_udp.set_register_message(
            display_name=APP.TINYPEDAL,
            connection_password=self._cfg["connection_password"],
            command_password=secrets.token_hex(10),  # use random password for read-only access
            realtime_update_interval=upd_update_interval,
        )

        while not _event_wait(update_interval):
            if not realtime_state.paused:

                if not reset:
                    reset = True
                    update_interval = 0.1

                    available_retry = total_retry
                    logger.info("UDP: CONNECTING: ACC Broadcasting Protocol (%s:%s)", udp_host, udp_port)

                if available_retry <= 0:
                    update_interval = 0.5
                else:
                    update_interval = 0.1
                    connection_success = False
                    try:
                        if acc_udp.clean_obsolete_client(
                            udp_host, udp_port, APP.TINYPEDAL, ACCConstants.LOG_PATH
                        ):  # wait 1s after cleaned clients
                            _event_wait(1.0)

                        with acc_udp.acc_udp_connect(
                            udp_host=udp_host,
                            udp_port=udp_port,
                            udp_output=udp_output,
                            connection_message=connection_message,
                            connection_timeout=connection_timeout,
                            blocking=False,
                            event=self._event,
                        ) as client:

                            available_retry = total_retry
                            connection_success = True
                            self.fetch_data(client, upd_update_interval / 1000, udp_output)

                    except (AttributeError, TypeError, IndexError, KeyError, ValueError, OSError, TimeoutError):
                        if connection_success:
                            available_retry = -1
                        else:
                            available_retry -= 1
                            update_interval = connection_retry_delay
                            logger.info("UDP: failed connecting to ACC Broadcasting Protocol, (%s/%s retries left)", available_retry, total_retry)

            else:
                if reset:
                    reset = False
                    update_interval = 0.5

    def fetch_data(self, client: socket.SocketType, update_interval: float, udp_output: acc_udp.UDPBroadcastOutput):
        """Fetch data"""
        _event_wait = self._event.wait
        _event_is_set = self._event.is_set
        connection_id = udp_output.registration.connectionId

        # Enable entry list sync
        udp_output.entryList.syncEntryList = True

        # Request track data, 11=outbound_type.REQUEST_TRACK_DATA
        logger.info("UDP: REQUESTED: REQUEST_TRACK_DATA")
        message = acc_udp.set_message(11, connection_id)
        client.send(message)

        # Set entry list message, 10=outbound_type.REQUEST_ENTRY_LIST
        sync_entry_message = acc_udp.set_message(10, connection_id)

        # Start update loop
        last_timestamp = 0.0
        last_car_entry_count = 0
        buffer_size = acc_udp.BroadcastingNetworkProtocol.BUFFER_SIZE

        while not _event_is_set() and not realtime_state.paused:
            # Get data
            try:
                recv_data = client.recv(buffer_size)
            except BlockingIOError:
                _event_wait(0.01)
                continue
            except OSError:
                buffer_size *= 2
                logger.info("UDP: INCREASED BUFFER SIZE: %s", buffer_size)
                continue

            # Parse data
            message_type = acc_udp.parse_udp_stream(recv_data, udp_output)

            # Wait interval after 2=InboundMessageTypes.REALTIME_UPDATE
            if message_type == 2:
                # Sync entry list
                if udp_output.entryList.syncEntryList:
                    current_timestamp = monotonic()
                    if current_timestamp - last_timestamp > 5:
                        last_timestamp = current_timestamp
                        client.send(sync_entry_message)
                        udp_output.entryList.syncEntryList = False
                        logger.info("UDP: REQUESTED: REQUEST_ENTRY_LIST")
                # Check car entry count
                car_entry_count = udp_output.entryList.carEntryCount
                if last_car_entry_count != car_entry_count:
                    last_car_entry_count = car_entry_count
                    logger.info("UDP: UPDATED: ENTRY_LIST (%s cars)", car_entry_count)
                # Wait
                _event_wait(update_interval)
