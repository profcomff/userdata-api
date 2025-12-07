from __future__ import annotations

from re import search

from fastapi_sqlalchemy import db
from sqlalchemy import String, cast, func, not_, or_

from userdata_api.exceptions import Forbidden, InvalidValidation, ObjectNotFound
from userdata_api.models.db import Category, Info, Param, Source, ViewType
from userdata_api.schemas.admin import UserDebugCardGet, UserDebugCardUpdate
from .user import patch_user_info as user_patch
from .user import get_user_info as user_get
from userdata_api.schemas.user import UserInfoUpdate, UserInfo


async def patch_user_info(
    new: UserDebugCardUpdate, user_id: int, user: dict[str, int | list[dict[str, str | int]]]
) -> None:
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
        update_info.append(UserInfo(
            category="Личная информация",
            param="Полное имя",
            value=new.full_name
        ))
    if new.student_card_number is not None:
        update_info.append(UserInfo(
            category="Учёба",
            param="Номер студенческого билета",
            value=new.student_card_number
        ))
    if update_info:
        update_request = UserInfoUpdate(
            items=update_info,
            source="admin"
        )
        await user_patch(update_request, user_id, user)

async def get_user_info(user_id: int, user: dict[str, int | list[dict[str, str | int]]]) -> UserDebugCardGet:
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
    user_info_response = await user_get(user_id, user)
    result = {
        "user_id": user_id,
        "full_name": None,
        "student_card_number": None,
        "union_card_number": None,
        "is_union_member": "false",
    }
    for item in user_info_response.items:
        if item.param == "Полное имя":
            result["full_name"] = item.value
        elif item.param == "Номер студенческого билета":
            result["student_card_number"] = item.value
        elif item.param == "Номер профсоюзного билета":
            result["union_card_number"] = item.value
        elif item.param == "Членство в профсоюзе":
            result["is_union_member"] = item.value
    return result
