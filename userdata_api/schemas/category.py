from pydantic import constr

from .base import Base
from .types.scope import Scope


class CategoryPost(Base):
    name: constr(min_length=1)
    read_scope: Scope | None = None
    update_scope: Scope | None = None


class CategoryPatch(Base):
    name: constr(min_length=1) | None = None
    read_scope: Scope | None = None
    update_scope: Scope | None = None


class CategoryGet(CategoryPost):
    id: int
