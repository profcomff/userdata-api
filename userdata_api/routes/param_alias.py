from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic.type_adapter import TypeAdapter
from sqlalchemy import not_

from userdata_api.exceptions import AlreadyExists, ObjectNotFound
from userdata_api.models.db import Param, ParamAlias, Source
from userdata_api.schemas.param_alias import ParamAliasGet, ParamAliasPatch, ParamAliasPost
from userdata_api.schemas.response_model import StatusResponseModel


param_alias = APIRouter(prefix="/category/{category_id}/param/{param_id}/alias", tags=["Param Alias"])


def _get_param(*, category_id: int, param_id: int) -> Param:
    param = (
        Param.query(session=db.session)
        .filter(
            Param.id == param_id,
            Param.category_id == category_id,
        )
        .one_or_none()
    )
    if not param:
        raise ObjectNotFound(Param, param_id)
    return param


def _get_param_alias(*, category_id: int, param_id: int, alias_id: int) -> ParamAlias:
    alias = (
        ParamAlias.query(session=db.session)
        .join(Param)
        .filter(
            ParamAlias.id == alias_id,
            ParamAlias.param_id == param_id,
            Param.category_id == category_id,
            not_(Param.is_deleted),
        )
        .one_or_none()
    )
    if not alias:
        raise ObjectNotFound(ParamAlias, alias_id)
    return alias


def _validate_source(source_id: int | None) -> None:
    if source_id is None:
        return
    source = Source.query(session=db.session).filter(Source.id == source_id).one_or_none()
    if not source:
        raise ObjectNotFound(Source, source_id)


def _check_alias_name_exists(name: str, *, alias_id: int | None = None) -> None:
    query = db.session.query(ParamAlias).filter(ParamAlias.name == name)
    if alias_id is not None:
        query = query.filter(ParamAlias.id != alias_id)
    if query.one_or_none():
        raise AlreadyExists(ParamAlias, name)


@param_alias.post("", response_model=ParamAliasGet)
async def create_param_alias(
    request: Request,
    category_id: int,
    param_id: int,
    alias_inp: ParamAliasPost,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.param.create"], allow_none=False, auto_error=True)),
) -> ParamAliasGet:
    """
    Создать алиас параметра.
    """
    _ = _get_param(category_id=category_id, param_id=param_id)
    _validate_source(alias_inp.source_id)
    _check_alias_name_exists(alias_inp.name)
    alias = ParamAlias.create(session=db.session, param_id=param_id, **alias_inp.model_dump())
    return ParamAliasGet.model_validate(alias)


@param_alias.get("/{alias_id}", response_model=ParamAliasGet)
async def get_param_alias(
    category_id: int,
    param_id: int,
    alias_id: int,
) -> ParamAliasGet:
    """
    Получить алиас параметра по айди.
    """
    alias = _get_param_alias(category_id=category_id, param_id=param_id, alias_id=alias_id)
    return ParamAliasGet.model_validate(alias)


@param_alias.get("", response_model=list[ParamAliasGet])
async def get_param_aliases(category_id: int, param_id: int) -> list[ParamAliasGet]:
    """
    Получить все алиасы параметра.
    """
    _ = _get_param(category_id=category_id, param_id=param_id)
    aliases = ParamAlias.query(session=db.session).filter(ParamAlias.param_id == param_id).all()
    type_adapter = TypeAdapter(list[ParamAliasGet])
    return type_adapter.validate_python(aliases)


@param_alias.patch("/{alias_id}", response_model=ParamAliasGet)
async def patch_param_alias(
    category_id: int,
    param_id: int,
    alias_id: int,
    alias_inp: ParamAliasPatch,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.param.update"], allow_none=False, auto_error=True)),
) -> ParamAliasGet:
    """
    Обновить алиас параметра.
    """
    alias = _get_param_alias(category_id=category_id, param_id=param_id, alias_id=alias_id)
    patch_data = alias_inp.model_dump(exclude_unset=True)
    if "name" in patch_data:
        _check_alias_name_exists(patch_data["name"], alias_id=alias.id)
    if "source_id" in patch_data:
        _validate_source(patch_data["source_id"])
    alias = ParamAlias.update(alias.id, session=db.session, **patch_data)
    return ParamAliasGet.model_validate(alias)


@param_alias.delete("/{alias_id}", response_model=StatusResponseModel)
async def delete_param_alias(
    request: Request,
    category_id: int,
    param_id: int,
    alias_id: int,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.param.delete"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Удалить алиас параметра.
    """
    _ = _get_param_alias(category_id=category_id, param_id=param_id, alias_id=alias_id)
    ParamAlias.delete(alias_id, session=db.session)
    return StatusResponseModel(status="Success", message="Param alias deleted", ru="Алиас параметра удален")
