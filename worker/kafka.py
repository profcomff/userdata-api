import json
import logging
import time

from confluent_kafka import Consumer, Message, TopicPartition
from event_schema.auth import UserLogin, UserLoginKey
from pydantic import ValidationError

from settings import get_settings
from userdata_api import __version__
from typing import Iterator, Any

log = logging.getLogger(__name__)


class KafkaConsumer:
    __dsn: str = get_settings().KAFKA_DSN  # Kafka cluster URL
    __devel: bool = True if __version__ == "dev" else False  # True if run locally else False
    __conf: dict[str, str] = {}  # Connect configuration
    __login: str | None = get_settings().KAFKA_LOGIN
    __password: str | None = get_settings().KAFKA_PASSWORD
    __group_id: str | None = get_settings().KAFKA_GROUP_ID # Consumer group id
    __topics: list[str] = get_settings().KAFKA_TOPICS # Kafka topics to listen
    _consumer: Consumer

    def __configurate(self) -> None:
        if self.__devel:
            self.__conf = {
                "bootstrap.servers": self.__dsn,
                'group.id': self.__group_id,
                'session.timeout.ms': 6000,
                'auto.offset.reset': 'earliest',
                'enable.auto.offset.store': False,
                'stats_cb': KafkaConsumer._stats_cb,
                'statistics.interval.ms': 1000,
                "auto.commit.interval.ms": 100,
            }
        else:
            self.__conf = {
                'bootstrap.servers': self.__dsn,
                'sasl.mechanisms': "PLAIN",
                'security.protocol': "SASL_PLAINTEXT",
                'sasl.username': self.__login,
                'sasl.password': self.__password,
                'group.id': self.__group_id,
                'session.timeout.ms': 6000,
                'auto.offset.reset': 'earliest',
                'enable.auto.offset.store': False,
                'stats_cb': KafkaConsumer._stats_cb,
                'statistics.interval.ms': 1000,
                "auto.commit.interval.ms": 100,
            }

    @staticmethod
    def _stats_cb(stats_json_str: str):
        stats_json = json.loads(stats_json_str)
        log.info('\nKAFKA Stats: {}\n'.format(stats_json))

    @staticmethod
    def _on_assign(consumer, partitions):
        log.info(f'Assignment: {partitions}')

    def connect(self) -> None:
        self._consumer = Consumer(self.__conf)
        self._consumer.subscribe(self.__topics, on_assign=KafkaConsumer._on_assign)

    def reconnect(self):
        del self._consumer
        self.connect()

    def __init__(self):
        self.__configurate()
        self.connect()

    def close(self):
        self._consumer.close()

    def listen(self) -> Iterator[tuple[Any, Any]]:
        try:
            while True:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    log.debug("Message is None")
                    continue
                if msg.error():
                    log.error(f"Message {msg=} reading triggered: {msg.error()}, Retrying...")
                    continue
                log.info('%% %s [%d] at offset %d\n' % (msg.topic(), msg.partition(), msg.offset()))
                try:
                    yield json.loads(msg.key()), json.loads(msg.value())
                    raise Exception
                except json.JSONDecodeError:
                    log.error("Json decode error occurred", exc_info=True)
                self._consumer.store_offsets(msg)
        finally:
            log.info("Consumer closed")
            self.close()
