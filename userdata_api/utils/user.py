from __future__ import annotations

from fastapi_sqlalchemy import db
from sqlalchemy import not_

from userdata_api.exceptions import Forbidden, ObjectNotFound
from userdata_api.models.db import Category, Info, Param, Source, ViewType
from userdata_api.schemas.user import UserInfoGet, UserInfoUpdate, UsersInfoGet


async def patch_user_info(new: UserInfoUpdate, user_id: int, user: dict[str, int | list[dict[str, str | int]]]) -> None:
    """
    Обновить информацию о пользователе в соотетствии с переданным токеном.

    Метод обновляет только информацию из источников `admin` и `user`

    Для обновления от имени админа нужен скоуп `userdata.info.admin`

    Для обновления от иимени пользователя необходима владениие ининформацией

    Обноввляет только инормацую созданную самим источником

    Для удаления информации передать None в соответствущем словаре из списка new.items

    :param new: модель запроса, в ней то на что будет изменена информация о пользователе
    :param user_id: Айди пользователя
    :param user: Сессия пользователя выполняющего запрос
    :return: get_user_info для текущего пользователя с переданными правами
    """
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    if new.source == "admin" and "userdata.info.admin" not in scope_names:
        raise Forbidden(
            "Admin source requires 'userdata.info.admin' scope",
            "Источник 'администратор' требует право 'userdata.info.admin'",
        )
    if new.source != "admin" and new.source != "user":
        raise Forbidden(
            "HTTP protocol applying only 'admin' and 'user' source",
            "Данный источник информации не обновляется через HTTP",
        )
    if new.source == "user" and user["id"] != user_id:
        raise Forbidden("'user' source requires information own", "Требуется владение информацией")
    for item in new.items:
        param = (
            db.session.query(Param)
            .join(Category)
            .filter(
                Param.name == item.param,
                Category.name == item.category,
                not_(Param.is_deleted),
                not_(Category.is_deleted),
            )
            .one_or_none()
        )
        if not param:
            raise ObjectNotFound(Param, item.param)
        if (
            param.category.update_scope is not None
            and param.category.update_scope not in scope_names
            and not (new.source == "user" and user["id"] == user_id)
        ):
            db.session.rollback()
            raise Forbidden(
                f"Updating category {param.category.name=} requires {param.category.update_scope=} scope",
                f"Обновление категории {param.category.name=} требует {param.category.update_scope=} права",
            )
        info = (
            db.session.query(Info)
            .join(Source)
            .filter(
                Info.param_id == param.id,
                Info.owner_id == user_id,
                Source.name == new.source,
                not_(Info.is_deleted),
            )
            .one_or_none()
        )
        if not info and item.value is None:
            continue
        if not info:
            source = Source.query(session=db.session).filter(Source.name == new.source).one_or_none()
            if not source:
                raise ObjectNotFound(Source, new.source)
            Info.create(
                session=db.session,
                owner_id=user_id,
                param_id=param.id,
                source_id=source.id,
                value=item.value,
            )
            continue
        if item.value is not None:
            if not param.changeable and "userdata.info.update" not in scope_names:
                db.session.rollback()
                raise Forbidden(
                    f"Param {param.name=} change requires 'userdata.info.update' scope",
                    f"Изменение {param.name=} параметра требует 'userdata.info.update' права",
                )
            info.value = item.value
            db.session.flush()
            continue
        if item.value is None:
            info.is_deleted = True
            db.session.flush()
            continue


async def get_user_info(user_id: int, user: dict[str, int | list[dict[str, str | int]]]) -> UserInfoGet:
    """
    Возвращает информауию о пользователе в соотетствии с переданным токеном.

    Пользователь может прочитать любую информацию о себе

    Токен с доступом к read_scope категории может получить доступ к данным категории у любых пользователей

    :param user_id: Айди пользователя
    :param user: Сессия выполняющего запрос данных
    :return: Список словарей содержащих категорию, параметр категории и значение этого параметра у польщователя
    """
    infos: list[Info] = (
        Info.query(session=db.session)
        .join(Param)
        .join(Category)
        .filter(Info.owner_id == user_id, not_(Param.is_deleted), not_(Category.is_deleted))
        .all()
    )
    if not infos:
        raise ObjectNotFound(Info, user_id)
    scope_names = [scope["name"] for scope in user["session_scopes"]]
    param_dict: dict[Param, list[Info] | Info | None] = {}
    for info in infos:
        ## Проверка доступов - нужен либо скоуп на категориию либо нужно быть овнером информации
        if info.category.read_scope and info.category.read_scope not in scope_names and user["id"] != user_id:
            continue
        if info.param not in param_dict.keys():
            param_dict[info.param] = [] if info.param.pytype == list[str] else None
        if info.param.type == ViewType.ALL:
            param_dict[info.param].append(info)
        elif (param_dict[info.param] is None) or (
            (info.param.type == ViewType.LAST and info.create_ts > param_dict[info.param].create_ts)
            or (
                info.param.type == ViewType.MOST_TRUSTED
                and (
                    param_dict[info.param].source.trust_level < info.source.trust_level
                    or (
                        param_dict[info.param].source.trust_level <= info.source.trust_level
                        and info.create_ts > param_dict[info.param].create_ts
                    )
                )
            )
        ):
            """
            Сюда он зайдет либо если параметру не соответствует никакой информации,
            либо если встретил более релевантную.

            Если у параметра отображение по доверию, то более релевантная
            - строго больше индекс доверия/такой же индекс доверия,
            но информация более поздняя по времени

            Если у параметра отображение по времени то более релевантная - более позднаяя
            """
            param_dict[info.param] = info
    result = []
    for item in param_dict.values():
        if isinstance(item, list):
            result.extend(
                [
                    {
                        "category": _item.category.name,
                        "param": _item.param.name,
                        "value": _item.value,
                    }
                    for _item in item
                ]
            )
        else:
            result.append(
                {
                    "category": item.category.name,
                    "param": item.param.name,
                    "value": item.value,
                }
            )
    return UserInfoGet(items=result)


async def get_users_info(
    user_ids: list[int],
    category_ids: list[int],
    user: dict[str, int | list[dict[str, str | int]]],
) -> UsersInfoGet:
    """
    Возвращает информацию о данных пользователей в указанных категориях

    :param user_ids: Список айди юзеров
    :param category_ids: Список айди необходимых категорий
    :param user: Сессия выполняющего запрос данных
    :return: Словарь, где ключи - айди юзеров, значение - словарь данных, как в get_user_info
    """
    scope_names = [scope["name"] for scope in user["session_scopes"]]
    infos: list[Info] = (
        Info.query(session=db.session)
        .join(Param)
        .join(Category)
        .filter(
            Info.owner_id.in_(user_ids),
            Param.category_id.in_(category_ids),
            not_(Param.is_deleted),
            not_(Category.is_deleted),
            not_(Info.is_deleted),
        )
        .all()
    )
    if not infos:
        raise ObjectNotFound(Info, user_ids)
    result = []
    for info in infos:
        if info.category.read_scope and info.category.read_scope not in scope_names:
            continue
        result.append(
            {
                "user_id": info.owner_id,
                "category": info.category.name,
                "param": info.param.name,
                "value": info.value,
            }
        )
    return UsersInfoGet(items=result)
