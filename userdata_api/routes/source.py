from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.exceptions import AlreadyExists
from userdata_api.models.db import Source
from userdata_api.schemas.response_model import StatusResponseModel
from userdata_api.schemas.source import SourceGet, SourcePatch, SourcePost
from userdata_api.utils.user_get import refreshing


source = APIRouter(prefix="/source", tags=["Source"])


@source.post("", response_model=SourceGet)
@refreshing
async def create_source(
    request: Request,
    source_inp: SourcePost,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.source.create"], allow_none=False, auto_error=True)),
) -> SourceGet:
    """
    Создать источник данных
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param source_inp: Моделька для создания
    :param _: Аутентификация
    :return: SourceGet - созданный источник
    """
    source = Source.query(session=db.session).filter(Source.name == source_inp.name).all()
    if source:
        raise AlreadyExists(Source, source_inp.name)
    return SourceGet.from_orm(Source.create(session=db.session, **source_inp.dict()))


@source.get("/{id}", response_model=SourceGet)
async def get_source(id: int) -> SourceGet:
    """
    Получить источник данных
    :param id: Айди источника
    :return: SourceGet - полученный источник
    """
    return SourceGet.from_orm(Source.get(id, session=db.session))


@source.get("", response_model=list[SourceGet])
async def get_sources() -> list[SourceGet]:
    """
    Получить все источники данных
    :return: list[SourceGet] - список источников данных
    """
    return parse_obj_as(list[SourceGet], Source.query(session=db.session).all())


@source.patch("/{id}", response_model=SourceGet)
@refreshing
async def patch_source(
    request: Request,
    id: int,
    source_inp: SourcePatch,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.source.update"], allow_none=False, auto_error=True)),
) -> SourceGet:
    """
    Обновить источник данных
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди обновляемого источника
    :param source_inp: Моделька для обновления
    :param _: Аутентификация
    :return: SourceGet - обновленный источник данных
    """
    return SourceGet.from_orm(Source.update(id, session=db.session, **source_inp.dict(exclude_unset=True)))


@source.delete("/{id}", response_model=StatusResponseModel)
@refreshing
async def delete_source(
    request: Request,
    id: int,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.source.delete"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Удалить источник данных
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди удаляемого источника
    :param _: Аутентфиикация
    :return: None
    """
    Source.delete(id, session=db.session)
    return StatusResponseModel(status="Success", message="Source deleted")
