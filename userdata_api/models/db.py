from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as DbEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from userdata_api.models.base import BaseDbModel


class ViewType(str, Enum):
    """
    Тип отображения пользоватльских данных в ответе `GET /user/{user_id}`
    ALL: {category: {param: [val1, val2, ...]}}
    LAST: {category: {param: last_modified_value}}
    MOST_TRUSTED: {category: {param: most_trusted_value}}
    """

    ALL: Final[str] = "all"
    LAST: Final[str] = "last"
    MOST_TRUSTED: Final[str] = "most_trusted"


class Category(BaseDbModel):
    """
    Категория - объеденение параметров пользовательских данных.
    Если параметром может быть, например, номер студенческого и номер профсоюзного,
    то категорией, их объединяющей, может быть "студенческая информация" или "документы"
    """

    name: Mapped[str] = mapped_column(String)
    read_scope: Mapped[str] = mapped_column(String, nullable=True)
    update_scope: Mapped[str] = mapped_column(String, nullable=True)
    create_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modify_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    params: Mapped[list[Param]] = relationship(
        "Param",
        foreign_keys="Param.category_id",
        back_populates="category",
        primaryjoin="and_(Category.id==Param.category_id, not_(Param.is_deleted))",
        lazy="joined",
    )


class Param(BaseDbModel):
    """
    Параметр - находится внутри категории,
    к нему можно задавать значение у конкретного пользователя.
    Например, параметрами может являться почта и номер телефона,
    а параметры эти могут лежать в категории "контакты"
    """

    visible_in_user_response: Mapped[bool] = mapped_column(Boolean, default=False)
    name: Mapped[str] = mapped_column(String)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey(Category.id))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    changeable: Mapped[bool] = mapped_column(Boolean, default=True)
    type: Mapped[ViewType] = mapped_column(DbEnum(ViewType, native_enum=False))
    create_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modify_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    category: Mapped[Category] = relationship(
        "Category",
        foreign_keys="Param.category_id",
        back_populates="params",
        primaryjoin="and_(Param.category_id==Category.id, not_(Category.is_deleted))",
        lazy="joined",
    )

    values: Mapped[list[Info]] = relationship(
        "Info",
        foreign_keys="Info.param_id",
        back_populates="param",
        primaryjoin="and_(Param.id==Info.param_id, not_(Info.is_deleted))",
        lazy="joined",
    )

    @property
    def pytype(self) -> type[str | list[str]]:
        return list[str] if self.type == ViewType.ALL else str


class Source(BaseDbModel):
    """
    Источник данных - субъект изменения польщовательских данных - тот, кто меняет данные
    В HTTP методах доступно только два источника - user/admin
    Субъект может менять только данные, созданные собой же.
    У источника есть уровень доверия, который влияет на вид ответа `GET /user/{user_id}`
    """

    name: Mapped[str] = mapped_column(String, unique=True)
    trust_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    create_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modify_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    values: Mapped[Info] = relationship(
        "Info",
        foreign_keys="Info.source_id",
        back_populates="source",
        primaryjoin="and_(Source.id==Info.source_id, not_(Info.is_deleted))",
        lazy="joined",
    )


class Info(BaseDbModel):
    """
    Значения параметров для конкретных польщзователей
    Если, например, телефон - параметр, то здесь указывается его значение для
    польщзователя(owner_id) - объекта изменения пользовательских данных
    """

    param_id: Mapped[int] = mapped_column(Integer, ForeignKey(Param.id))
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey(Source.id))
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    create_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modify_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    param: Mapped[Param] = relationship(
        "Param",
        foreign_keys="Info.param_id",
        back_populates="values",
        primaryjoin="and_(Info.param_id==Param.id, not_(Param.is_deleted))",
        lazy="joined",
    )

    source: Mapped[Source] = relationship(
        "Source",
        foreign_keys="Info.source_id",
        back_populates="values",
        primaryjoin="and_(Info.source_id==Source.id, not_(Source.is_deleted))",
        lazy="joined",
    )

    @hybrid_property
    def category(self) -> Category:
        return self.param.category
