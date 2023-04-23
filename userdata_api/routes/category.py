from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.exceptions import AlreadyExists
from userdata_api.models.db import Category, Scope
from userdata_api.schemas.category import CategoryGet, CategoryPatch, CategoryPost
from userdata_api.utils.user import refreshing


category = APIRouter(prefix="/category", tags=["Category"])


@category.post("", response_model=CategoryGet)
@refreshing
async def create_category(
    request: Request,
    category_inp: CategoryPost,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userinfo.category.create"], allow_none=False, auto_error=True)),
) -> CategoryGet:
    """
    Создать категорию пользовательских данных. Получить категорию можно будет со скоупами, имена которых в category_inp.scopes
    Ручка обновит документацию
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param category_inp: Принимаемая моделька
    :param _: Аутентификация
    :return: CategoryGet
    """
    if Category.query(session=db.session).filter(Category.name == category_inp.name).all():
        raise AlreadyExists(Category, category_inp.name)
    scopes = []
    category = Category.create(session=db.session, name=category_inp.name)
    for scope in category_inp.scopes:
        scopes.append(Scope.create(name=scope, category_id=category.id, session=db.session).name)
    return CategoryGet(id=category.id, name=category.name, scopes=scopes)


@category.get("/{id}", response_model=CategoryGet)
async def get_category(
    id: int,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userinfo.category.read"], allow_none=False, auto_error=True)),
) -> dict[str, str | int]:
    """
    Получить категорию
    :param id: Айди категории
    :param _: Аутентфикация
    :return: Категорию со списком скоупов, которые нужны для получения пользовательских данных этой категории
    """
    category = Category.get(id, session=db.session)
    return {"id": category.id, "name": category.name, "scopes": [_scope.name for _scope in category.scopes]}


@category.get("", response_model=list[CategoryGet])
async def get_categories(
    _: dict[str, str] = Depends(UnionAuth(scopes=["userinfo.category.read"], allow_none=False, auto_error=True))
) -> list[CategoryGet]:
    """
    Получить все категории
    :param _: Аутентифиуация
    :return: Список категорий. В каждой ноде списка - информация о скоупах, которые нужны для получения пользовательских данных этой категории
    """
    result: list[dict[str, Any]] = []
    for category in Category.query(session=db.session).all():
        result.append({"id": category.id, "name": category.name, "scopes": [_scope.name for _scope in category.scopes]})
    return parse_obj_as(list[CategoryGet], result)


@category.patch("/{id}", response_model=CategoryGet)
@refreshing
async def patch_category(
    request: Request,
    id: int,
    category_inp: CategoryPatch,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userinfo.category.update"], allow_none=False, auto_error=True)),
) -> CategoryGet:
    """
    Обновить категорию
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди обновляемой категории
    :param category_inp: Моделька обновления
    :param _: Аутентификация
    :return: CategoryGet - обновленную категорию
    """
    category: Category = Category.get(id, session=db.session)
    category.name = category_inp.name or category.name
    scopes = set(category_inp.scopes) if category_inp.scopes else set()
    db_scopes = {_scope for _scope in category.scopes}
    to_create: set[str] = set()
    to_delete: set[Scope] = set()
    for scope in db_scopes:
        if scope.name not in scopes:
            to_delete.add(scope)
    for scope in scopes:
        if scope not in {_scope.name for _scope in db_scopes}:
            to_create.add(scope)
    for scope in to_create:
        Scope.create(name=scope, category_id=category.id, session=db.session)
    for scope in to_delete:
        db.session.delete(scope)
    db.session.commit()
    del category
    category = Category.get(id, session=db.session)
    return CategoryGet(
        **{"name": category.name, "id": category.id, "scopes": [scope.name for scope in category.scopes]}
    )


@category.delete("/{id}")
@refreshing
async def delete_category(
    request: Request,
    id: int,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userinfo.category.delete"], allow_none=False, auto_error=True)),
) -> None:
    """
    Удалить категорию
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди удаляемой категории
    :param _: Аутентификация
    :return: None
    """
    category: Category = Category.get(id, session=db.session)
    for scope in category.scopes:
        Scope.delete(scope.id, session=db.session)
    Category.delete(id, session=db.session)
    return None
