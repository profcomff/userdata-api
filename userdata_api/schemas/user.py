from pydantic import constr, field_validator

from .base import Base


class UserInfo(Base):
    category: str
    param: str
    value: str | None = None


class UserInfoGet(Base):
    items: list[UserInfo]

    @classmethod
    @field_validator("items")
    def unique_validator(cls, v):
        _iter_category = (row.category for row in v)
        if len(frozenset(_iter_category)) != len(tuple(_iter_category)):
            raise ValueError("Category list is not unique")
        _iter_params = (row.param for row in v)
        if len(frozenset(_iter_params)) != len(tuple(_iter_params)):
            raise ValueError("Category list is not unique")
        return v


class UserInfoUpdate(UserInfoGet):
    source: constr(min_length=1)
