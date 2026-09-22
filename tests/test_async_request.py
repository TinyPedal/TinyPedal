"""
Test Asynchronous Request
"""

import asyncio
import logging
import sys
from time import perf_counter
from typing import Awaitable

sys.path.append(".")
from tinypedal.async_request import get_response, localhost_resolve, set_header_get

logger = logging.getLogger(__name__)


async def _print_result(test_func: Awaitable):
    """Test result"""
    start = perf_counter()
    result = await test_func
    end = perf_counter()
    is_timeout = " (timeout)" if not result else " (done)"
    logger.info("%s(s)%s, %s", end - start, is_timeout, result)


async def _test_async_get(timeout: float):
    """Test run"""
    req1 = set_header_get("/rest/sessions/setting/SESSSET_race_timescale")
    req2 = set_header_get("/rest/sessions/weather")
    rf2_host = await localhost_resolve({"localhost", "127.0.0.1"}, 5397, timeout)
    task_rf2 = [
        _print_result(get_response(req1, rf2_host, 5397, timeout)),  # RF2
        _print_result(get_response(req2, rf2_host, 5397, timeout)),  # RF2
    ]
    req3 = set_header_get("/rest/sessions/weather")
    req4 = set_header_get("/rest/strategy/pitstop-estimate")
    lmu_host = await localhost_resolve({"localhost", "127.0.0.1"}, 6397, timeout)
    task_lmu = [
        _print_result(get_response(req3, lmu_host, 6397, timeout)),  # LMU
        _print_result(get_response(req4, lmu_host, 6397, timeout)),  # LMU
    ]
    await asyncio.gather(*task_rf2, *task_lmu)


if __name__ == "__main__":
    # Add logger
    test_handler = logging.StreamHandler()
    logger.setLevel(logging.INFO)
    logger.addHandler(test_handler)
    logger.info(__doc__)

    asyncio.run(_test_async_get(1))
