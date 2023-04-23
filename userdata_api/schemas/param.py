from pydantic import constr

from userdata_api.models.db import Type

from .base import Base


class ParamPost(Base):
    name: constr(min_length=1)
    is_required: bool
    changeable: bool
    type: Type


class ParamPatch(Base):
    name: constr(min_length=1) | None
    is_required: bool | None
    changeable: bool | None
    type: Type | None


class ParamGet(ParamPost):
    id: int
    category_id: int
