"""
Test ACC sharedmemory API connector
"""

import logging
import sys
from time import sleep

sys.path.append(".")
sys.path.append("thirdparty")

from tinypedal.adapter.acc_sharedmemory import ACCInfo


def test_api():
    """API test run"""
    # Add logger
    test_handler = logging.StreamHandler()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(test_handler)
    logger.info(__doc__)

    # Test run
    SEPARATOR = "=" * 50
    logger.info("Test API - Start")
    info = ACCInfo()
    info.setMode(1)  # set direct access
    info.setPlayerOverride(True)  # enable player override
    info.setPlayerIndex(0)  # set player index to 0
    info.start()
    sleep(0.2)

    logger.info(SEPARATOR)
    logger.info("Test API - Restart")
    info.stop()
    info.setMode()  # set copy access
    info.setPlayerOverride()  # disable player override
    info.start()

    logger.info(SEPARATOR)
    logger.info("Test API - Read")
    version = info.accStaticInfo.smVersion
    driver = info.accStaticInfo.playerName
    track = info.accStaticInfo.trackName
    logger.info("version: %s", version if version else "not running")
    logger.info("driver : %s", driver if version else "not running")
    logger.info("track  : %s", track if version else "not running")

    logger.info(SEPARATOR)
    logger.info("Test API - Close")
    info.stop()


if __name__ == "__main__":
    test_api()
