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


class Type(str, Enum):
    ALL: Final[str] = "all"
    LAST: Final[str] = "last"
    MOST_TRUSTED: Final[str] = "most_trusted"


class Category(BaseDbModel):
    name: Mapped[str] = mapped_column(String)
    read_scope: Mapped[str] = mapped_column(String, nullable=True)
    update_scope: Mapped[str] = mapped_column(String, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    params: Mapped[list[Param]] = relationship(
        "Param",
        foreign_keys="Param.category_id",
        back_populates="category",
        primaryjoin="and_(Category.id==Param.category_id, not_(Param.is_deleted))",
    )


class Param(BaseDbModel):
    name: Mapped[str] = mapped_column(String)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey(Category.id))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    changeable: Mapped[bool] = mapped_column(Boolean, default=True)
    type: Mapped[Type] = mapped_column(DbEnum(Type, native_enum=False), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    category: Mapped[Category] = relationship(
        "Category",
        foreign_keys="Param.category_id",
        back_populates="params",
        primaryjoin="and_(Param.category_id==Category.id, not_(Category.is_deleted))",
    )

    infos: Mapped[Info] = relationship(
        "Info",
        foreign_keys="Info.param_id",
        back_populates="param",
        primaryjoin="and_(Param.id==Info.param_id, not_(Info.is_deleted))",
    )

    @property
    def pytype(self) -> type:
        match self.type:
            case Type.LAST:
                return str
            case Type.MOST_TRUSTED:
                return str
            case Type.ALL:
                return list[str]


class Source(BaseDbModel):
    name: Mapped[str] = mapped_column(String)
    trust_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    infos: Mapped[Info] = relationship(
        "Info",
        foreign_keys="Info.source_id",
        back_populates="source",
        primaryjoin="and_(Source.id==Info.source_id, not_(Info.is_deleted))",
    )


class Info(BaseDbModel):
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
        back_populates="infos",
        primaryjoin="and_(Info.param_id==Param.id, not_(Param.is_deleted))",
    )

    source: Mapped[Source] = relationship(
        "Source",
        foreign_keys="Info.source_id",
        back_populates="infos",
        primaryjoin="and_(Info.source_id==Source.id, not_(Source.is_deleted))",
    )

    @hybrid_property
    def category(self) -> Category:
        return self.param.category
