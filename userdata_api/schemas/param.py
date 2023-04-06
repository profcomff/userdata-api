from pydantic import constr

from userdata_api.models.db import Type

from .base import Base


class ParamPost(Base):
    name: constr(min_length=1)
    category_id: int
    is_required: bool
    changeable: bool
    type: Type


class ParamPatch(Base):
    name: constr(min_length=1) | None
    category_id: int | None
    is_required: bool | None
    changeable: bool | None
    type: Type | None


class ParamGet(ParamPost):
    id: int
