from pydantic import constr

from .base import Base


class ParamAliasPost(Base):
    name: constr(min_length=1)
    source_id: int | None = None


class ParamAliasPatch(Base):
    name: constr(min_length=1) | None = None
    source_id: int | None = None


class ParamAliasGet(ParamAliasPost):
    id: int
    param_id: int
    source_name: str | None = None
