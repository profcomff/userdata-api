from pydantic import conint, constr

from .base import Base


class SourcePost(Base):
    name: constr(min_length=1)
    trust_level: conint(gt=0, lt=11)


class SourcePatch(Base):
    name: constr(min_length=1) | None
    trust_level: conint(gt=0, lt=11) | None


class SourceGet(SourcePost):
    id: int
