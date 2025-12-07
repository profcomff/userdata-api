from .base import Base


class UserDebugCardGet(Base):
    user_id: int
    full_name: str | None = None
    student_card_number: str | None = None
    union_card_number: str | None = None
    is_union_member: str


class UserDebugCardUpdate(Base):
    full_name: str | None = None
    student_card_number: str | None = None
