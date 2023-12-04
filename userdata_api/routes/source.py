from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic.type_adapter import TypeAdapter

from userdata_api.exceptions import AlreadyExists
from userdata_api.models.db import Source
from userdata_api.schemas.response_model import StatusResponseModel
from userdata_api.schemas.source import SourceGet, SourcePatch, SourcePost


source = APIRouter(prefix="/source", tags=["Source"])


@source.post("", response_model=SourceGet, description="Создать источник данных")
async def create_source(
    request: Request,
    source_inp: SourcePost,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.source.create"], allow_none=False, auto_error=True)),
) -> SourceGet:
    """
    Создать источник данных
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param source_inp: Моделька для создания
    :param _: Аутентификация
    :return: SourceGet - созданный источник
    """
    source = Source.query(session=db.session).filter(Source.name == source_inp.name).all()
    if source:
        raise AlreadyExists(Source, source_inp.name)
    return SourceGet.model_validate(Source.create(session=db.session, **source_inp.dict()))


@source.get("/{id}", response_model=SourceGet, description="Получить источник данных")
async def get_source(id: int) -> SourceGet:
    """
    Получить источник данных
    \f
    :param id: Айди источника
    :return: SourceGet - полученный источник
    """
    return SourceGet.model_validate(Source.get(id, session=db.session))


@source.get("", response_model=list[SourceGet], description='Получить все источники данных')
async def get_sources() -> list[SourceGet]:
    """
    Получить все источники данных
    \f
    :return: list[SourceGet] - список источников данных
    """
    type_adapter = TypeAdapter(list[SourceGet])
    return type_adapter.validate_python(Source.query(session=db.session).all())


@source.patch("/{id}", response_model=SourceGet, description='Обновить источник данных')
async def patch_source(
    request: Request,
    id: int,
    source_inp: SourcePatch,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.source.update"], allow_none=False, auto_error=True)),
) -> SourceGet:
    """
    Обновить источник данных
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди обновляемого источника
    :param source_inp: Моделька для обновления
    :param _: Аутентификация
    :return: SourceGet - обновленный источник данных
    """
    return SourceGet.model_validate(Source.update(id, session=db.session, **source_inp.dict(exclude_unset=True)))


@source.delete("/{id}", response_model=StatusResponseModel, description='Удалить источник данных')
async def delete_source(
    request: Request,
    id: int,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.source.delete"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Удалить источник данных
    \f
    :param request: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :param id: Айди удаляемого источника
    :param _: Аутентфиикация
    :return: None
    """
    Source.delete(id, session=db.session)
    return StatusResponseModel(status="Success", message="Source deleted")
