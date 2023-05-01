import asyncio
from functools import wraps
from typing import Awaitable, Callable, TypeVar

from fastapi import FastAPI
from fastapi_sqlalchemy import db
from sqlalchemy.orm import Session
from starlette.requests import Request
from typing_extensions import ParamSpec

from userdata_api.exceptions import Forbidden, ObjectNotFound
from userdata_api.models.db import Category, Info, Param, Source, Type
from userdata_api.schemas.user import user_interface


async def get_user_info(
    session: Session, user_id: int, user: dict[str, int | list[dict[str, str | int]]]
) -> dict[str, dict[str, str]]:
    """
    Получить пользовательские данные, в зависимости от переданных скоупов.
    :param user: Сессия запрашиваемого данные
    :param session: Соеденение с БД
    :param user_id: Айди овнера информации(пользователя)
    :return: Словарь пользовательских данных, которым есть доступ у токена
    """
    infos: list[Info] = Info.query(session=session).filter(Info.owner_id == user_id).all()
    param_dict: dict[Param, list[Info]] = {}
    scope_names = [scope["name"] for scope in user["session_scopes"]]
    for info in infos:
        ## Проверка доступов - нужен либо скоуп на категориию либо нуужно быть овнером информации
        if info.category.read_scope and info.category.read_scope not in scope_names:
            continue
        if info.param not in param_dict.keys():
            param_dict[info.param] = []
        param_dict[info.param].append(info)
    result = {}
    for param, v in param_dict.items():
        if param.category.name not in result.keys():
            result[param.category.name] = {}
        if param.type == Type.ALL:
            result[param.category.name][param.name] = [_v.value for _v in v]
        elif param.type == Type.LAST:
            q: Info = (
                Info.query(session=session)
                .filter(Info.owner_id == user_id, Info.param_id == param.id)
                .order_by(Info.modify_ts.desc())
                .first()
            )
            result[param.category.name][param.name] = q.value
        elif param.type == Type.MOST_TRUSTED:
            q: Info = (
                Info.query(session=session)
                .join(Source)
                .filter(Info.owner_id == user_id, Info.param_id == param.id)
                .order_by(Source.trust_level.desc())
                .order_by(Info.modify_ts.desc())
                .first()
            )
            result[param.category.name][param.name] = q.value
    return result


async def __param(user_id: int, category_name: str, param_name: str, values: list[dict[str, str | int]]) -> None:
    param_id = (
        db.session.query(Param.id)
        .join(Category)
        .filter(Param.name == param_name)
        .filter(Category.name == category_name)
        .one_or_none()
    )[0]
    for info in db.session.query(Info).filter(Info.owner_id == user_id, Info.param_id == param_id).all():
        Info.delete(info.id, session=db.session)
    sources = Source.query(session=db.session).filter(Source.name.in_([value.get("source") for value in values])).all()
    assert len(sources) == len(frozenset([value.get("source") for value in values]))
    source_dict: dict[str, Source] = {}
    for source in sources:
        source_dict[source.name] = source
    for value in values:
        Info.create(
            session=db.session,
            owner_id=user_id,
            param_id=param_id,
            source_id=source_dict[value["source"]].id,
            value=value["value"],
        )


async def __category(user_id: int, category_name: str, category_dict: dict[str, list[dict[str, str | int]]]):
    async with asyncio.TaskGroup() as tg:
        for k, v in category_dict.items():
            tg.create_task(__param(user_id, category_name, k, v))
    return


async def process_post_model(
    user_id: int,
    model: dict[str, dict[str, list[dict[str, str | int]]] | int],
    user: dict[str, int | list[dict[str, str | int]]],
):
    scope_names = [scope["name"] for scope in user["session_scopes"]]
    exc = None
    async with asyncio.TaskGroup() as tg:
        for k, v in model.items():
            category = Category.query(session=db.session).filter(Category.name == k).one_or_none()
            if not category:
                exc = ObjectNotFound(Category, k)
                break
            if category.update_scope not in scope_names:
                exc = Forbidden(category.name, category.update_scope)
                break
            else:
                tg.create_task(__category(user_id, k, v))
    if exc:
        raise exc
    db.session.commit()
    return


T = TypeVar("T")
P = ParamSpec("P")


def refreshing(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """
    Декоратор сообщает, что функция обновляет возможные поля пользователя.
    Обновляет поля пользователя в запросах (например, в ручке `GET /user/{user_id}`) и документацию OpenAPI
    Первым аргументом ручки должен быть request.
    """

    @wraps(fn)
    async def decorated(request: Request, *args: P.args, **kwargs: P.kwargs) -> T:
        app: FastAPI = request.app
        _res = await fn(request, *args, **kwargs)
        await user_interface.refresh(db.session)
        app.openapi_schema = None
        return _res

    return decorated
