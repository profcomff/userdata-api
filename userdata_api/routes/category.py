from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.exceptions import AlreadyExists
from userdata_api.models.db import Category
from userdata_api.schemas.category import CategoryGet, CategoryPatch, CategoryPost
from userdata_api.schemas.response_model import StatusResponseModel


category = APIRouter(prefix="/category", tags=["Category"])


@category.post("", response_model=CategoryGet)
async def create_category(
    request: Request,
    category_inp: CategoryPost,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.create"], allow_none=False, auto_error=True)),
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
    category = Category.create(session=db.session, **category_inp.dict())
    return CategoryGet.from_orm(category)


@category.get("/{id}", response_model=CategoryGet)
async def get_category(
    id: int,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.read"], allow_none=False, auto_error=True)),
) -> CategoryGet:
    """
    Получить категорию
    :param id: Айди категории
    :param _: Аутентфикация
    :return: Категорию со списком скоупов, которые нужны для получения пользовательских данных этой категории
    """
    category = Category.get(id, session=db.session)
    return CategoryGet.model_validate(category)


@category.get("", response_model=list[CategoryGet])
async def get_categories(
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.read"], allow_none=False, auto_error=True))
) -> list[CategoryGet]:
    """
    Получить все категории
    :param _: Аутентифиуация
    :return: Список категорий. В каждой ноде списка - информация о скоупах, которые нужны для получения пользовательских данных этой категории
    """
    return parse_obj_as(list[CategoryGet], Category.query(session=db.session).all())


@category.patch("/{id}", response_model=CategoryGet)
async def patch_category(
    request: Request,
    id: int,
    category_inp: CategoryPatch,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.update"], allow_none=False, auto_error=True)),
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
    return CategoryGet.from_orm(Category.update(id, session=db.session, **category_inp.dict(exclude_unset=True)))


@category.delete("/{id}", response_model=StatusResponseModel)
async def delete_category(
    request: Request,
    id: int,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.delete"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Удалить категорию
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди удаляемой категории
    :param _: Аутентификация
    :return: None
    """
    _: Category = Category.get(id, session=db.session)
    Category.delete(id, session=db.session)
    return StatusResponseModel(status="Success", message="Category deleted")
