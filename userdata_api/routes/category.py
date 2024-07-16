from typing import Literal

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Query, Request
from fastapi_sqlalchemy import db
from pydantic.type_adapter import TypeAdapter

from userdata_api.exceptions import AlreadyExists
from userdata_api.models.db import Category
from userdata_api.schemas.category import CategoryGet, CategoryPatch, CategoryPost
from userdata_api.schemas.response_model import StatusResponseModel


category = APIRouter(prefix="/category", tags=["Category"])


@category.post(
    "",
    response_model=CategoryGet,
)
async def create_category(
    request: Request,
    category_inp: CategoryPost,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.create"], allow_none=False, auto_error=True)),
) -> CategoryGet:
    """
    Создать категорию пользовательских данных. Получить категорию можно будет со скоупами, имена которых в category_inp.scopes
    Ручка обновит документацию

    Scopes: `["userdata.category.create"]`
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param category_inp: Принимаемая моделька
    :param _: Аутентификация
    :return: CategoryGet
    """
    if Category.query(session=db.session).filter(Category.name == category_inp.name).all():
        raise AlreadyExists(Category, category_inp.name)
    category = Category.create(session=db.session, **category_inp.dict())
    return CategoryGet.model_validate(category)


@category.get("/{id}", response_model=CategoryGet)
async def get_category(id: int) -> CategoryGet:
    """
    Получить категорию
    \f
    :param id: Айди категории
    :param _: Аутентфикация
    :return: Категорию со списком скоупов, которые нужны для получения пользовательских данных этой категории
    """
    category = Category.get(id, session=db.session)
    return CategoryGet.model_validate(category)


@category.get("", response_model=list[CategoryGet], response_model_exclude_none=True)
async def get_categories(query: list[Literal["param"]] = Query(default=[])) -> list[CategoryGet]:
    """
    Получить все категории
    \f
    :param query: Лист query параметров.
    Если ничего не указано то вернет просто список категорий
    Параметр 'param' - если указан, то в каждой категории будет список ее параметров
    :param _: Аутентифиуация
    :return: Список категорий. В каждой ноде списка - информация о скоупах, которые нужны для получения пользовательских данных этой категории
    """
    result = []
    for category in Category.query(session=db.session).all():
        to_append = category.dict()
        if "param" in query:
            to_append["params"] = []
            for param in category.params:
                to_append["params"].append(param.dict())
        result.append(to_append)

    type_adapter = TypeAdapter(list[CategoryGet])
    return type_adapter.validate_python(result)


@category.patch("/{id}", response_model=CategoryGet)
async def patch_category(
    request: Request,
    id: int,
    category_inp: CategoryPatch,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.update"], allow_none=False, auto_error=True)),
) -> CategoryGet:
    """
    Обновить категорию

    Scopes: `["userdata.category.update"]`
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди обновляемой категории
    :param category_inp: Моделька обновления
    :param _: Аутентификация
    :return: CategoryGet - обновленную категорию
    """
    category: Category = Category.get(id, session=db.session)
    return CategoryGet.model_validate(Category.update(id, session=db.session, **category_inp.dict(exclude_unset=True)))


@category.delete("/{id}", response_model=StatusResponseModel)
async def delete_category(
    request: Request,
    id: int,
    _: dict[str, str] = Depends(UnionAuth(scopes=["userdata.category.delete"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Удалить категорию
    
    Scopes: `["userdata.category.delete"]`
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди удаляемой категории
    :param _: Аутентификация
    :return: None
    """
    _: Category = Category.get(id, session=db.session)
    Category.delete(id, session=db.session)
    return StatusResponseModel(status="Success", message="Category deleted", ru="Категория удалена")
