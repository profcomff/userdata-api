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

    Если не указать значение параметра, то ничего не обновится, но если указать,
    то обновится полностью вся информация, конкретного параметра для этого польщователя.

    Пример:

    До обновления ответ на `GET /user/{id}` с полным списком прав был таким:

    {
      "category1": {
        "param1": [
          "old_value1",
          "old_value2"
        ],
        "param2": [
          "old_value3"
        ]
      },
      "category2": {
        "param3": "old_value4"
      }
    }

    Запрос на обновление будет такой:

    {
      "category1": {
        "param1": [
          {
            "value": "test_vk",
            "source": "vk"
          },
          {
            "value": "test_admin",
            "source": "admin"
          }
        ]
      },
      "category3": {
        "param4": [
          {
            "value": "test_new",
            "source": "admin"
          }
        ]
      }
    }

    В таком случае в категории category1 полностью обновится param1. В категории category1 param2 останется нетронутым.
    Для юзера создастся запись с param4 из категории category3

    После обновления ответ на `GET /user/{id}` с полным списком прав будет таким:

    {
      "category1": {
        "param1": [
          "test_vk",
          "test_admin"
        ],
        "param2": [
          "old_value3"
        ]
      },
      "category2": {
        "param3": "old_value4"
      }
    }


    :param request:
    :param user_id:
    :param _:
    :param user:
    :return:
    """
    js = await request.json()
    await process_post_model(user_id, js, user)
    res = await get_user_info_func(db.session, user_id, user)
    return Response(content=json.dumps(res), media_type="application/json")
