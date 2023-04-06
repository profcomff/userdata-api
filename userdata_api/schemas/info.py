from pydantic import constr

from .base import Base


class InfoPost(Base):
    param_id: int
    source_id: int
    value: constr(min_length=1)
    owner_id: int


class InfoPatch(Base):
    param_id: int | None
    source_id: int | None
    value: constr(min_length=1) | None
    owner_id: int | None


class InfoGet(InfoPost):
    id: int
