from pydantic import constr

from userdata_api.models.db import ViewType

from .base import Base


class ParamPost(Base):
    is_public: bool = False
    visible_in_user_response: bool = True
    name: constr(min_length=1)
    is_required: bool
    changeable: bool
    type: ViewType
    validation: constr(min_length=1) | None = None


class ParamPatch(Base):
    is_public: bool = False
    visible_in_user_response: bool = True
    name: constr(min_length=1) | None = None
    is_required: bool | None = None
    changeable: bool | None = None
    type: ViewType | None = None
    validation: constr(min_length=1) | None = None


class ParamGet(ParamPost):
    id: int
    category_id: int
