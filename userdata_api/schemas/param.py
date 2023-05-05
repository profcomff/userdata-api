from pydantic import constr

from userdata_api.models.db import ViewType

from .base import Base


class ParamPost(Base):
    name: constr(min_length=1)
    is_required: bool
    changeable: bool
    type: ViewType


class ParamPatch(Base):
    name: constr(min_length=1) | None
    is_required: bool | None
    changeable: bool | None
    type: ViewType | None


class ParamGet(ParamPost):
    id: int
    category_id: int
