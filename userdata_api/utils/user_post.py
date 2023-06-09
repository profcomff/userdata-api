from __future__ import annotations

from dataclasses import dataclass

from fastapi_sqlalchemy import db
from sqlalchemy.orm import Session

from userdata_api.exceptions import Forbidden, ObjectNotFound
from userdata_api.models.db import Category, Info, Param, Source


@dataclass
class QueryData:
    """
    Датакласс для хранения информации из БД, нужной для разбора тела запроса

    category_map: хэш-маша категорий: query_data.category_map[category_name]

    param_map: хэш-мапа параметров внутри категорий: query_data.param_map[category_name][param_name].
    Если параметр лежит вне этой категории, то кинет KeyError

    info_map: хэш-мапа инфоррмации об объекте запроса. Ключ - кортеж из айди параметра и айди источника иинформации:
    query_data.info_map[(1, 2)]

    source: источник данных
    """

    category_map: dict[str, Category]
    param_map: dict[str, dict[str, Param]]
    info_map: dict[tuple[int, int], Info]
    source: Source


async def __param(
    user_id: int,
    category_name: str,
    query_data: QueryData,
    user: dict[str, int | list[dict[str, str | int]]],
    *,
    param_name: str,
    value: str | None,
) -> None:
    """
    Низший уровень разбора запроса. Разбирает обновление параметра внутри категории
    :param user_id: Объект запроса
    :param category_name: Имя разбираемой категории
    :param query_data: Данные из БД для разбора запроса
    :param param_name: Имя разбираемого параметра
    :param value: Новое значение разбираемого параметра
    :return: None
    """
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    param: Param = query_data.param_map.get(category_name).get(param_name, None)
    info = query_data.info_map.get((param.id, query_data.source.id), None)
    if not info and value is None:
        return
    if not info:
        Info.create(
            session=db.session,
            owner_id=user_id,
            param_id=param.id,
            source_id=query_data.source.id,
            value=value,
        )
        return
    if value is not None:
        if not param.changeable and "userdata.info.update" not in scope_names:
            rollback_and_raise_exc(
                db.session, Forbidden(f"Param {param.name=} change requires 'userdata.info.update' scope")
            )
        info.value = value
        return
    info.is_deleted = True
    db.session.flush()
    return


async def __category(
    user_id: int,
    category_name: str,
    category_dict: dict[str, str],
    query_data: QueryData,
    user: dict[str, int | list[dict[str, str | int]]],
) -> None:
    """
    Разбор словаря категории в теле запроса на изменение пользовательских данных

    То есть, функция разбирает одно из значений тела запроса
    :param user_id: Объект запроса
    :param category: Имя разбираемой категории
    :param category_dict: Словарь параметров запроса разбираемой категории
    :param query_data: Данные из БД, нужные для разбора запроса
    :param user: Субъект запроса
    :return: None
    """
    for k, v in category_dict.items():
        param = query_data.param_map.get(category_name).get(k, None)
        if not param:
            rollback_and_raise_exc(db.session, ObjectNotFound(Param, k))
        await __param(user_id, category_name, query_data, user, param_name=k, value=v)


async def make_query(user_id: int, model: dict[str, dict[str, str] | int]) -> QueryData:
    """
    Запросить все нужные данные из БД с тем, чтобы потом использовать из в ходе разбора тела запроса
    :param user_id: Айди объекта запроса
    :param model: Тело запроса
    :return: Датакласс, содержащий все необходимые данные:
    хэш-мапа категорий, хеш-мапа параметров, источник, хэм-мапа информации
    """
    param_map, category_map = {}, {}
    info_map = {}
    param_ids = []
    categories = Category.query(session=db.session).filter(Category.name.in_(model.keys())).all()
    for category in categories:
        category_map[category.name] = category
        param_map[category.name] = {param.name: param for param in category.params}
        param_ids.extend([param.id for param in category.params])
    source = Source.query(session=db.session).filter(Source.name == model["source"]).one_or_none()
    infos = Info.query(session=db.session).filter(Info.param_id.in_(param_ids), Info.owner_id == user_id).all()
    for info in infos:
        info_map[(info.param.id, info.source_id)] = info
    return QueryData(category_map=category_map, param_map=param_map, source=source, info_map=info_map)


def rollback_and_raise_exc(session: Session, exc: Exception) -> None:
    """
    Откатить измненения в БД вызванные текущим разбором и кинуть ошибку
    :param session: Соединение с БДД
    :param exc: Ошибка, которую надо выкинуть
    :return: None
    """
    session.rollback()
    raise exc


async def post_model(
    user_id: int,
    model: dict[str, dict[str, str] | int],
    query_data: QueryData,
    user: dict[str, int | list[dict[str, str | int]]],
    session: Session,
) -> None:
    """
    Разобрать первый уровень тела запроса на иизменение пользовательских данных

    Запрещает изменение в случае отсутствия права
    на изменение какой либо из запрошенных категорий одновременно
    с тем, что субъект запроса не является его объектом
    :param user_id: Объект запроса
    :param model: Тело запроса
    :param query_data: Данные из БД, которые нужны для дальнейшего разбора запроса
    :param user: Субъект запроса
    :param session: Соединение с БД
    :return: None
    """
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    for k, v in model.items():
        if k == "source":
            continue
        category = query_data.category_map.get(k, None)
        if not category:
            rollback_and_raise_exc(session, ObjectNotFound(Category, k))
        if category.update_scope not in scope_names and not (model["source"] == "user" and user["user_id"] == user_id):
            rollback_and_raise_exc(
                session, Forbidden(f"Updating category {category.name=} requires {category.update_scope=} scope")
            )
        await __category(user_id, category.name, v, query_data, user)


async def process_post_model(
    user_id: int,
    model: dict[str, dict[str, str] | int],
    user: dict[str, int | list[dict[str, str | int]]],
) -> None:
    """
    Обработать запрос изменения польщоательских данных

    Возможны изменения только из источников admin и user
    :param user_id: объект изменения пользовавтельских данных
    :param model: тело запроса
    :param user: судъект изменения польщовательских данных
    :return: None
    """
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    query_data = await make_query(user_id, model)
    if model["source"] == "admin" and "userdata.info.admin" not in scope_names:
        raise Forbidden(f"Admin source requires 'userdata.info.update' scope")
    if model["source"] != "admin" and model["source"] != "user":
        raise Forbidden("HTTP protocol applying only 'admin' and 'user' source")
    if model["source"] == "user" and user["user_id"] != user_id:
        raise Forbidden(f"'user' source requires information own")
    return await post_model(user_id, model, query_data, user, db.session)
