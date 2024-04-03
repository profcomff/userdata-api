from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic.type_adapter import TypeAdapter

from userdata_api.exceptions import AlreadyExists, ObjectNotFound
from userdata_api.models.db import Category, Param
from userdata_api.schemas.param import ParamGet, ParamPatch, ParamPost
from userdata_api.schemas.response_model import StatusResponseModel


param = APIRouter(prefix="/category/{category_id}/param", tags=["Param"])


@param.post("", response_model=ParamGet)
async def create_param(
    request: Request,
    category_id: int,
    param_inp: ParamPost,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.param.create"], allow_none=False, auto_error=True)),
) -> ParamGet:
    """
    Создать поле внутри категории. Ответ на пользовательские данные будет такой {..., category: {...,param: '', ...}}
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param category_id: Айди котегории в которой создавать параметр
    :param param_inp: Модель для создания
    :param _: Аутентификация
    :return: ParamGet - созданный параметр
    """
    Category.get(category_id, session=db.session)
    if Param.query(session=db.session).filter(Param.category_id == category_id, Param.name == param_inp.name).all():
        raise AlreadyExists(Param, param_inp.name)
    return ParamGet.model_validate(Param.create(session=db.session, **param_inp.dict(), category_id=category_id))


@param.get("/{id}", response_model=ParamGet)
async def get_param(
    id: int,
    category_id: int,
    _: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True)),
) -> ParamGet:
    """
    Получить параметр по айди
    \f
    :param id: Айди параметра
    :param category_id: айди категории в которой этот параметр находится
    :return: ParamGet - полученный параметр
    :param _: Аутентификация
    """

    res = Param.query(session=db.session).filter(Param.id == id, Param.category_id == category_id).one_or_none()
    if not res:
        raise ObjectNotFound(Param, id)
    if res.is_hidden:
        category_scopes = set(
            Category.query(session=db.session).filter(Category.id == category_id).one_or_none().read_scope
        )
        user_scopes = set([scope["name"].lower() for scope in _["session_scopes"]])
        if category_scopes - user_scopes:
            raise ObjectNotFound(Param, id)
        return ParamGet.model_validate(res)
    return ParamGet.model_validate(res)


@param.get("", response_model=list[ParamGet])
async def get_params(category_id: int) -> list[ParamGet]:
    """
    Получить все параметры категории
    \f
    :param category_id: Айди категории
    :return: list[ParamGet] - список полученных параметров
    """
    type_adapter = TypeAdapter(list[ParamGet])
    return type_adapter.validate_python(Param.query(session=db.session).filter(Param.category_id == category_id).all())


@param.patch("/{id}", response_model=ParamGet)
async def patch_param(
    request: Request,
    id: int,
    category_id: int,
    param_inp: ParamPatch,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.param.update"], allow_none=False, auto_error=True)),
) -> ParamGet:
    """
    Обновить параметр внутри категории
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди обновляемого параметра
    :param category_id: Адйи категории в которой находится параметр
    :param param_inp: Модель для создания параметра
    :param _: Аутентификация
    :return: ParamGet- Обновленный параметр
    """
    if category_id:
        Category.get(category_id, session=db.session)
    if category_id:
        return ParamGet.from_orm(
            Param.update(id, session=db.session, **param_inp.dict(exclude_unset=True), category_id=category_id)
        )
    return ParamGet.model_validate(Param.update(id, session=db.session, **param_inp.dict(exclude_unset=True)))


@param.delete("/{id}", response_model=StatusResponseModel)
async def delete_param(
    request: Request,
    id: int,
    category_id: int,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.param.delete"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Удалить параметр внутри категории
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди удаляемого параметра
    :param category_id: Айди категории в которой находится удлаляемый параметр
    :param _: Аутентификация
    :return: None
    """
    res: Param = Param.query(session=db.session).filter(Param.id == id, Param.category_id == category_id).one_or_none()
    if not res:
        raise ObjectNotFound(Param, id)
    res.is_deleted = True
    db.session.commit()
    return StatusResponseModel(status="Success", message="Param deleted")
