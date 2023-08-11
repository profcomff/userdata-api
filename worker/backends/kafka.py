import json
import logging

from confluent_kafka import Consumer, Message, TopicPartition
from event_schema.auth import UserLogin, UserLoginKey
from pydantic import ValidationError

from settings import get_settings
from userdata_api import __version__

from .kafkameta import KafkaMeta

log = logging.getLogger(__name__)


class KafkaConsumer(KafkaMeta):
    __dsn: str = get_settings().KAFKA_DSN
    __devel: bool = True if __version__ == "dev" else False
    __conf: dict[str, str] = {}
    __login: str | None = get_settings().KAFKA_LOGIN
    __password: str | None = get_settings().KAFKA_PASSWORD
    __group_id: str | None = get_settings().KAFKA_GROUP_ID
    __topics: list[str] = get_settings().KAFKA_TOPICS
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


    def __init__(self):
        self.__configurate()
        self._consumer = Consumer(self.__conf)
        self._consumer.subscribe(["test-user-login"], on_assign=KafkaConsumer._on_assign)


    def _parse_message(self, msg: Message) -> tuple[int, UserLogin]:
        user_info = UserLogin.model_validate(json.loads(msg.value()))
        user_id = UserLoginKey.model_validate(json.loads(msg.key())).user_id
        return user_id, user_info

    def close(self):
        self._consumer.close()

    def run(self) -> None:
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
                    user_id, user_info = self._parse_message(msg)
                except (ValidationError, json.JSONDecodeError):
                    log.error(f"Message skipped due to validation error", exc_info=True)
                    self._consumer.store_offsets(msg)
                    continue
                self._patch_user_info(user_info, user_id)
                self._consumer.store_offsets(msg)
        finally:
            log.info("Consumer closed")
            self.close()
