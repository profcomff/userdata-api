import string
from typing import Any, Generator

from pydantic.validators import AnyCallable, str_validator


CallableGenerator = Generator[AnyCallable, None, None]


class Scope(str):
    """
    Класс для валидации строки скоупа
    Скоуп должен быть строкой
    Скоуп должен быть не пустой строкой
    Скоуп не может начинаться с точки или заканчиваться ей
    Скоуп должен состоять только из букв, точек и подчеркиваний
    """

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.update(type='string', format='scope')

    @classmethod
    def __get_validators__(cls) -> CallableGenerator:
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, val: str) -> str:
        if val == "":
            raise ValueError("Empty string are not allowed")
        val = str(val).strip().lower()
        if val[0] == "." or val[-1] == ".":
            raise ValueError("Dot can not be leading or closing")
        if len(set(val) - set(string.ascii_lowercase + "._")) > 0:
            raise ValueError("Only letters, dot and underscore allowed")
        return val
