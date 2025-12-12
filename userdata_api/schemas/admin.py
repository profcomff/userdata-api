from .base import Base


class UserCardGet(Base):
    user_id: int
    full_name: str | None = None
    student_card_number: str | None = None
    union_card_number: str | None = None
    is_union_member: bool


class UserCardUpdate(Base):
    full_name: str | None = None
    student_card_number: str | None = None
