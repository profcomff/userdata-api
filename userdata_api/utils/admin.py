from __future__ import annotations

from fastapi_sqlalchemy import db

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import Info, Param, Source
from userdata_api.schemas.admin import UserCardGet, UserCardUpdate
from userdata_api.schemas.user import UserInfo, UserInfoUpdate

from .user import patch_user_info as user_patch


async def patch_user_info(new: UserCardUpdate, user_id: int, user: dict[str, int | list[dict[str, str | int]]]) -> None:
    """
    Обновить информацию о пользователе в соотетствии с переданным токеном.

    Метод обновляет только информацию из источников `admin`.

    Для обновления от имени админа нужен скоуп `userdata.info.admin`

    :param new: модель запроса, в ней то, на что будет изменена информация о пользователе
    :param user_id: Айди пользователя
    :param user: Сессия пользователя выполняющего запрос
    :return: get_user_info для текущего пользователя с переданными правами
    """
    update_info = []
    if new.full_name is not None:
        update_info.append(UserInfo(category="Личная информация", param="Полное имя", value=new.full_name))
    if new.student_card_number is not None:
        update_info.append(
            UserInfo(category="Учёба", param="Номер студенческого билета", value=new.student_card_number)
        )
    if update_info:
        update_request = UserInfoUpdate(items=update_info, source="admin")
        await user_patch(update_request, user_id, user)


async def get_user_info(user_id: int, user: dict[str, int | list[dict[str, str | int]]]) -> UserCardGet:
    """
    Получить профсоюзную информацию пользователя для админки.

    :param user_id: Айди пользователя, информацию о котором запрашиваем
    :param user: Сессия пользователя, выполняющего запрос (должен иметь права администратора)
    :return: Словарь с данными пользователя:
        - user_id: ID пользователя
        - full_name: Полное имя (из параметра "Полное имя")
        - student_card_number: Номер студенческого билета (из параметра "Номер студенческого билета")
        - union_card_number: Номер профсоюзного билета (из параметра "Номер профсоюзного билета")
        - is_union_member: Статус мэтчинга (из параметра "Членство в профсоюзе")
        - last_check_timestamp: Дата последней проверки
    """
    users = db.session.query(Info).filter(Info.owner_id == user_id).first()
    if not users:
        raise ObjectNotFound(Info, user_id)
    full_name = (
        db.session.query(Info)
        .join(Info.param)
        .join(Info.source)
        .filter(Info.owner_id == user_id, Param.name == "Полное имя")
        .order_by(Source.trust_level.desc())
        .order_by(Info.create_ts.desc())
        .first()
    )
    is_union_member = (
        db.session.query(Info)
        .join(Info.param)
        .join(Info.source)
        .filter(Info.owner_id == user_id, Param.name == "Членство в профсоюзе")
        .order_by(Source.trust_level.desc())
        .order_by(Info.create_ts.desc())
        .first()
    )
    student_card_number = (
        db.session.query(Info)
        .join(Info.param)
        .join(Info.source)
        .filter(Info.owner_id == user_id, Param.name == "Номер студенческого билета")
        .order_by(Source.trust_level.desc())
        .order_by(Info.create_ts.desc())
        .first()
    )
    union_card_number = (
        db.session.query(Info)
        .join(Info.param)
        .join(Info.source)
        .filter(Info.owner_id == user_id, Param.name == "Номер профсоюзного билета")
        .order_by(Source.trust_level.desc())
        .order_by(Info.create_ts.desc())
        .first()
    )
    result = {
        "user_id": user_id,
        "full_name": full_name.value if full_name else None,
        "student_card_number": student_card_number.value if student_card_number else None,
        "union_card_number": union_card_number.value if union_card_number else None,
        "is_union_member": is_union_member.value if is_union_member else "false",
    }
    return result
