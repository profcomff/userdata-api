from pydantic import constr

from .base import Base
from .types.scope import Scope


class CategoryPost(Base):
    name: constr(min_length=1)
    scopes: list[Scope]


class CategoryPatch(Base):
    name: constr(min_length=1) | None
    scopes: list[Scope] | None


class CategoryGet(CategoryPost):
    id: int
