import logging
from logging.config import fileConfig
from pathlib import Path

from worker.backends.kafka import KafkaConsumer


path = Path(__file__).resolve().parents[1]


fileConfig(f"{path}/logging_worker.conf")

log = logging.getLogger(__name__)

consumer = KafkaConsumer()

if __name__ == '__main__':
    while True:
        try:
            consumer.run()
        except KeyboardInterrupt:
            log.info("Worker stopped by signal", exc_info=False)
            exit(0)
        except Exception:
            log.error("Error occurred", exc_info=True)
