import logging
from typing import Any

import pydantic
from event_schema.auth import UserLogin, UserLoginKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import get_settings
from worker.kafka import KafkaConsumer

from .user import patch_user_info


log = logging.getLogger(__name__)
settings = get_settings()
consumer = KafkaConsumer()

_engine = create_engine(str(settings.DB_DSN), pool_pre_ping=True, isolation_level="AUTOCOMMIT")
_Session = sessionmaker(bind=_engine)


def process_message(key: Any, value: Any) -> tuple[UserLoginKey | None, UserLogin | None]:
    try:
        return UserLoginKey.model_validate(key), UserLogin.model_validate(value)
    except pydantic.ValidationError:
        log.error(f"Validation error occurred, {key=}, {value=}", exc_info=False)
        return None, None


def process():
    while 1:
        try:
            for k, v in consumer.listen():
                processed_k, processed_v = process_message(k, v)
                if not (processed_k and processed_v):
                    continue
                patch_user_info(processed_v, processed_k.user_id, session=_Session())
        except Exception:
            log.error("Error occurred", exc_info=True)
            consumer.reconnect()
        except KeyboardInterrupt:
            log.warning("Worker stopped by user")
            exit(0)
