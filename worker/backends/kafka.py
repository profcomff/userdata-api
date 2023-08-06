import json
import logging
from pprint import pformat

from confluent_kafka import Consumer, KafkaException, Message
from event_schema.auth import UserLogin, UserLoginKey
from pydantic import ValidationError
from sqlalchemy import not_
from sqlalchemy.orm import Session

from settings import get_settings
from userdata_api import __version__
from userdata_api.models.db import Category, Info, Param, Source

from .pg import PgSession


log = logging.getLogger(__name__)


class KafkaConsumer:
    __dsn: str = get_settings().KAFKA_DSN
    __devel: bool = True if __version__ == "dev" else False
    __conf: dict[str, str] = {}
    __login: str | None = get_settings().KAFKA_LOGIN
    __password: str | None = get_settings().KAFKA_PASSWORD
    __group_id: str | None = get_settings().KAFKA_GROUP_ID
    __topics: list[str] = get_settings().KAFKA_TOPICS
    _pg = PgSession()
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
        log.info('\nKAFKA Stats: {}\n'.format(pformat(stats_json)))

    @staticmethod
    def _on_assign(consumer, partitions):
        print("ASDasdasd")
        log.info(f'Assignment: {partitions}')

    def __init__(self):
        self.__configurate()
        self._consumer = Consumer(self.__conf, debug='fetch', logger=log)
        if diff := set(self.__topics) - set(self._consumer.list_topics()):
            assert False, f"Topics from {diff=} doesn't exists"
        self._consumer.subscribe(self.__topics, on_assign=KafkaConsumer._on_assign)

    def close(self) -> None:
        self._consumer.close()

    def _parse_message(self, msg: Message) -> tuple[int, UserLogin]:
        user_info = UserLogin.model_validate(msg.value())
        user_id = UserLoginKey.model_validate(msg.key()).user_id
        return user_id, user_info

    def _patch_user_info(self, new: UserLogin, user_id: int) -> None:
        with self._pg as pg:
            for item in new.items:
                param = (
                    pg.query(Param)
                    .join(Category)
                    .filter(
                        Param.name == item.param,
                        Category.name == item.category,
                        not_(Param.is_deleted),
                        not_(Category.is_deleted),
                    )
                    .one_or_none()
                )
                if not param:
                    pg.rollback()
                    log.error(f"Param {item.param=} not found")
                    return
                info = (
                    pg.query(Info)
                    .join(Source)
                    .filter(
                        Info.param_id == param.id,
                        Info.owner_id == user_id,
                        Source.name == new.source,
                        not_(Info.is_deleted),
                    )
                    .one_or_none()
                )
                if not info and item.value is None:
                    continue
                if not info:
                    source = Source.query(session=pg).filter(Source.name == new.source).one_or_none()
                    if not source:
                        pg.rollback()
                        log.warning(f"Source {new.source=} not found")
                        return
                    Info.create(
                        session=pg,
                        owner_id=user_id,
                        param_id=param.id,
                        source_id=source.id,
                        value=item.value,
                    )
                    continue
                if item.value is not None:
                    info.value = item.value
                    pg.flush()
                    continue
                if item.value is None:
                    info.is_deleted = True
                    pg.flush()
                    continue

    def run(self) -> None:
        try:
            while True:
                msg = self._consumer.poll(timeout=1.0)
                print(msg)
                if msg is None:
                    continue
                if msg.error():
                    log.error(f"Message {msg=} reading triggered: {msg.error()}, Retrying...")
                    continue
                log.info('%% %s [%d] at offset %d\n' % (msg.topic(), msg.partition(), msg.offset()))
                try:
                    user_id, user_info = self._parse_message(msg)
                except ValidationError:
                    log.error(f"Message skipped due to validation error", exc_info=True)
                    self._consumer.store_offsets(msg)
                    continue
                self._patch_user_info(user_info, user_id)
                self._consumer.store_offsets(msg)
        finally:
            self.close()
