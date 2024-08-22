from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Query
from fastapi_sqlalchemy import db

from userdata_api.models.db import Category, Info
from userdata_api.schemas.response_model import StatusResponseModel
from userdata_api.schemas.user import UserInfoGet, UserInfoUpdate, UsersInfoGet
from userdata_api.utils.user import get_user_info as get
from userdata_api.utils.user import get_users_info_batch as get_users
from userdata_api.utils.user import patch_user_info as patch


user = APIRouter(prefix="/user", tags=["User"])


@user.get("/{id}", response_model=UserInfoGet)
async def get_user_info(
    id: int,
    additional_data: list[str] = Query(default=[]),
    user: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True)),
) -> UserInfoGet:
    """
    Получить информацию о пользователе
    \f
    :param id: Айди овнера информации(пользователя)
    :additional_data: список невидимых по дефолту параметров
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

    return UserInfoGet.model_validate(await get(id, user, additional_data))


@user.post("/{id}", response_model=StatusResponseModel)
async def update_user(
    new_info: UserInfoUpdate,
    id: int,
    user: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Обновить информацию о пользователе.
    Объект - пользователь, информацию которого обновляют
    Субъект - пользователь, который обновляет - источник

    Если не указать параметр внутри категории, то ничего не обновится, если указать что-то,
    то либо создастся новая запись(в случае, если она отсутствовала у данного источника), либо отредактируется
    старая. Если в значении параметра указан None, то соответствующая информациия удаляется из данного источника

    Обновлять через эту ручку можно только от имени источников admin и user.

    Чтобы обновить от имени админиа, надо иметь скоуп `userdata.info.admin`
    Чтобы обновить неизменяемую информацию надо обладать скоупом `userdata.info.update`
    Для обновления своей информации(источник `user`) не нужны скоупы на обновление соответствующих категорий
    Для обновления чужой информации от имени админа(источник `admin`)
    нужны скоупы на обновление всех указанных в теле запроса категорий пользовательских данных данных
    \f
    :param request: Запрос из fastapi
    :param user_id: Айди объекта обновленя
    :param _: Модель запроса
    :param user:
    :return:
    """
    await patch(new_info, id, user)
    return StatusResponseModel(status="Success", message="User patch succeeded", ru="Изменение успешно")


@user.get("", response_model=UsersInfoGet, response_model_exclude_unset=True)
async def get_users_info(
    users: list[int] = Query(),
    categories: list[int] = Query(),
    user: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.info.admin"], allow_none=False, auto_error=True)),
    additional_data: list[str] = Query(default=[]),
) -> UsersInfoGet:
    """
    Получить информацию о пользователях.
    :param users: список id юзеров, про которых нужно вернуть информацию
    :param categories: список id категорий, параметры которых нужно вернуть
    :return: список данных о пользователях и данных категориях
    """
    return UsersInfoGet.model_validate(await get_users(users, categories, user, additional_data))
