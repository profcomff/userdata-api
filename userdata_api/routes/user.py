import json
from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from starlette.responses import Response

from userdata_api.schemas.user import user_interface
from userdata_api.utils.user_get import get_user_info as get_user_info_func
from userdata_api.utils.user_post import process_post_model


user = APIRouter(prefix="/user", tags=["UserGet"])


@user.get("/{id}", response_model=user_interface.UserGet)
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
    return Response(content=json.dumps(res), media_type="application/json")


@user.post("/{user_id}", response_model=user_interface.UserGet)
async def update_user(
    request: Request,
    user_id: int,
    _: user_interface.UserUpdate,
    user: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True)),
) -> user_interface.UserGet:
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
    Для обновления чужой информации от имени админа(источник  `admin`)
    нужны скоупы на обновление всех указанных в теле запроса категорий пользовательских данных данных


    Пример:

    До обновления ответ на `GET /user/{id}` с полным списком прав был таким:

    {
      "category1": {
        "param1": [
          "old_value1", ##admin source
          "old_value2" ##vk source
        ],
        "param2": [
          "old_value3" ##vk source
        ]
      },
      "category2": {
        "param3": "old_value4", ##admin source
        "param5": "old_value5" ##admin source
      }
    }

    Запрос на обновление будет такой:

    {
      "source": "admin",
      "category1": {
        "param1": "upd1",
        "param2": "upd2"
      },
      "category2": {
        "param5": null,
      },
      "category3": {
        "param4": "new",
      }
    }

    В таком случае обновится

    После обновления ответ на `GET /user/{id}` с полным списком прав будет таким:

    {
      "category1": {
        "param1": [
          "upd1", ##admin source
          "old_value2" ##vk source
        ],
        "param2": [
          "old_value3" ##vk source
          "upd2" ##admin source
        ]
      },
      "category2": {
        "param3": "old_value4", ##admin source
      }
      "category3":{
        "param4": "new"
      }
    }


    :param request: Запрос из fastapi
    :param user_id: Айди объекта обновленя
    :param _: Модель запроса
    :param user:
    :return:
    """
    js = await request.json()
    await process_post_model(user_id, js, user)
    res = await get_user_info_func(db.session, user_id, user)
    return Response(content=json.dumps(res), media_type="application/json")
