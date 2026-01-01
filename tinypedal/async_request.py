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
Asynchronous request
"""

from __future__ import annotations

from asyncio import StreamReader, open_connection, wait_for
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Awaitable

# Default limit from asyncio.open_connection is 2 ** 16
# Lower limit to avoid getting incomplete data
BUFFER_LIMIT = 32768  # 2 ** 15


def set_header_get(uri: str = "/", host: str = "localhost", *headers: str) -> bytes:
    """Set GET request header"""
    # "Accept: application/json"
    extra_headers = "\r\n" + "\r\n".join(headers) if headers else ""
    return f"GET {uri} HTTP/1.1\r\nHost: {host}{extra_headers}\r\n\r\n".encode()


async def parse_response(reader: StreamReader) -> bytes:
    """Parse response"""
    # Get headers
    header_bytes = await reader.readuntil(b"\r\n\r\n")
    if b"200" not in header_bytes:  # check http status code
        return b""
    # Get non-chunked data
    if b"chunked" not in header_bytes:
        # Get body length
        body_length = 0
        pos_beg = header_bytes.find(b"Content-Length")
        if pos_beg >= 0:
            try:
                pos_beg += 15  # offset
                pos_end = header_bytes.find(b"\r\n", pos_beg)
                body_length = int(header_bytes[pos_beg:pos_end])
            except (AttributeError, TypeError, IndexError, ValueError):
                body_length = 0
        if body_length <= 0:
            return b""
        if body_length <= BUFFER_LIMIT:
            return await reader.read(body_length)
        # Exceeded buffer limit
        temp_bytes = bytearray()
        while body_length > 0:
            temp_bytes.extend(await reader.read(BUFFER_LIMIT))
            body_length -= BUFFER_LIMIT
        return bytes(temp_bytes)
    # Get chunked data
    temp_bytes = bytearray()
    while (await reader.readuntil()) != b"0\r\n":  # end chunk
        temp_bytes[-2:] = await reader.readuntil()  # cut off CRLF
    return bytes(temp_bytes)


@asynccontextmanager
async def http_get(request: bytes, host: str, port: int, time_out: float):
    """Async request - HTTP get response"""
    writer = None
    try:
        reader, writer = await wait_for(open_connection(host, port), time_out)
        writer.write(request)
        await writer.drain()
        yield await wait_for(parse_response(reader), time_out)
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


@asynccontextmanager
async def https_get(request: bytes, host: str, port: int, time_out: float):
    """Async request - HTTPS get response"""
    writer = None
    try:
        reader, writer = await wait_for(open_connection(host, port, ssl=True), time_out)
        writer.write(request)
        await writer.drain()
        yield await wait_for(parse_response(reader), time_out)
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


async def get_response(request: bytes, host: str, port: int, time_out: float, ssl: bool = False) -> bytes:
    """Get response data (bytes)"""
    try:
        func_get = https_get if ssl else http_get
        async with func_get(request, host, port, time_out) as raw_bytes:
            return raw_bytes
    except (ConnectionError, TimeoutError, OSError, BaseException):
        return b""


async def _print_result(test_func: Awaitable):
    """Test result"""
    start = perf_counter()
    result = await test_func
    end = perf_counter()
    is_timeout = " (timeout)" if not result else " (done)"
    print(f"{end - start:.6f}s{is_timeout},", result)


async def _test_async_get(timeout: float):
    """Test run"""
    req1 = set_header_get("/rest/sessions/setting/SESSSET_race_timescale")
    req2 = set_header_get("/rest/sessions/weather")
    req3 = set_header_get("/rest/sessions")
    req4 = set_header_get("/rest/garage/getPlayerGarageData")
    task_rf2 = [
        _print_result(get_response(req1, "localhost", 5397, timeout)),  # RF2
        _print_result(get_response(req2, "localhost", 5397, timeout)),  # RF2
    ]
    task_lmu = [
        _print_result(get_response(req3, "localhost", 6397, timeout)),  # LMU
        _print_result(get_response(req4, "localhost", 6397, timeout)),  # LMU
    ]
    await asyncio.gather(*task_rf2, *task_lmu)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_test_async_get(1))
