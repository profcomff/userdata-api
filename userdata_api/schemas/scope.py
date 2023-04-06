from .base import Base
from .types.scope import Scope


class ScopePost(Base):
    name: Scope


class ScopePatch(Base):
    name: Scope | None


class ScopeGet(ScopePost):
    id: int
