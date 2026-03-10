import logging
import os
import time

from apscheduler.schedulers.background import BackgroundScheduler

from ai_wildfire_tracker.ingest.firms import ingest_firms
from ai_wildfire_tracker.ingest.noaa_hms import ingest_noaa_hms

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

FIRMS_INTERVAL_MIN = int(os.getenv("FIRMS_INTERVAL_MIN", "30"))
NOAA_INTERVAL_MIN = int(os.getenv("NOAA_INTERVAL_MIN", "30"))


def safe_ingest_firms():
    try:
        logger.info("Starting NASA FIRMS ingest job")
        ingest_firms()
        logger.info("NASA FIRMS ingest job completed")
    except Exception:
        logger.exception("NASA FIRMS ingest job failed")


def safe_ingest_noaa():
    try:
        logger.info("Starting NOAA HMS ingest job")
        ingest_noaa_hms()
        logger.info("NOAA HMS ingest job completed")
    except Exception:
        logger.exception("NOAA HMS ingest job failed")


def main():
    scheduler = BackgroundScheduler()

    scheduler.add_job(safe_ingest_firms, "interval", minutes=FIRMS_INTERVAL_MIN)
    scheduler.add_job(safe_ingest_noaa, "interval", minutes=NOAA_INTERVAL_MIN)

    scheduler.start()
    logger.info(
        "Scheduler started. FIRMS every %s min | NOAA every %s min",
        FIRMS_INTERVAL_MIN,
        NOAA_INTERVAL_MIN,
    )

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
