from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.exceptions import AlreadyExists
from userdata_api.models.db import Source
from userdata_api.schemas.source import SourceGet, SourcePatch, SourcePost
from userdata_api.schemas.user import refreshing


source = APIRouter(prefix="/source", tags=["Source"])


@source.post("", response_model=SourceGet)
@refreshing
async def create_source(
    request: Request,
    source_inp: SourcePost,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userinfo.source.create"], allow_none=False, auto_error=True)),
) -> SourceGet:
    source = Source.query(session=db.session).filter(Source.name == source_inp.name).all()
    if source:
        raise AlreadyExists(Source, source_inp.name)
    return SourceGet.from_orm(Source.create(session=db.session, **source_inp.dict()))


@source.get("/{id}", response_model=SourceGet)
async def get_source(id: int) -> SourceGet:
    return SourceGet.from_orm(Source.get(id, session=db.session))


@source.get("", response_model=list[SourceGet])
async def get_sources() -> list[SourceGet]:
    return parse_obj_as(list[SourceGet], Source.query(session=db.session).all())


@source.patch("/{id}", response_model=SourceGet)
@refreshing
async def patch_source(
    request: Request,
    id: int,
    source_inp: SourcePatch,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userinfo.source.update"], allow_none=False, auto_error=True)),
) -> SourceGet:
    return SourceGet.from_orm(Source.update(id, session=db.session, **source_inp.dict(exclude_unset=True)))


@source.delete("/{id}")
@refreshing
async def delete_source(
    request: Request,
    id: int,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userinfo.source.delete"], allow_none=False, auto_error=True)),
) -> None:
    Source.delete(id, session=db.session)
