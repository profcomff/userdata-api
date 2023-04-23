import json
from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends
from fastapi_sqlalchemy import db
from starlette.responses import Response

from userdata_api.schemas.user import user_interface
from userdata_api.utils.user import get_user_info as get_user_info_func


user = APIRouter(prefix="/user", tags=["User"])


@user.get("/{id}", response_model=user_interface.User)
async def get_user_info(
    id: int, user: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True))
):
    """
    Получить информацию о польщователе
    :param id: Айди овнера информации(пользователя)
    :param user: Аутентфикация
    :return: Словарь, ключи - категории на которые хватило прав(овнеру не нужны права, он получает всё).
    Значения - словари, ключи которых - имена параметров,
    внутри соответствующих категорий, значния - значения этих параметров у конкретного пользователя
    Например:
    {student: {card: 123, group: 342},
    profcomff: {card: 1231231, is_member: True},
    ...
    }
    """
    await user_interface.refresh(db.session)
    res = await get_user_info_func(db.session, id, user)
    user_interface.User(**res)
    return Response(content=json.dumps(res), media_type="application/json")
