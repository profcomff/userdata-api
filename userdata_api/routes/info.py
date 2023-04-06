from fastapi import APIRouter
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.models.db import Info, Param, Source
from userdata_api.schemas.info import InfoGet, InfoPatch, InfoPost


info = APIRouter(prefix="/info", tags=["Info"])


@info.post("", response_model=InfoGet)
async def create_info(info_inp: InfoPost) -> InfoGet:
    Source.get(info_inp.source_id, session=db.session)
    Param.get(info_inp.param_id, session=db.session)
    return InfoGet.from_orm(Info.create(session=db.session, **info_inp.dict()))


@info.get("/{id}", response_model=InfoGet)
async def get_info(id: int) -> InfoGet:
    return InfoGet.from_orm(Info.get(id, session=db.session))


@info.get("", response_model=list[InfoGet])
async def get_infos() -> list[InfoGet]:
    return parse_obj_as(list[InfoGet], Info.query(session=db.session).all())


@info.patch("/{id}", response_model=InfoGet)
async def patch_info(id: int, info_inp: InfoPatch) -> InfoGet:
    if info_inp.param_id:
        Param.get(info_inp.param_id, session=db.session)
    if info_inp.source_id:
        Source.get(info_inp.source_id, session=db.session)
    return InfoGet.from_orm(Info.update(id, session=db.session, **info_inp.dict(exclude_unset=True)))


@info.delete("/{id}")
async def delete_info(id: int) -> None:
    Info.delete(id, session=db.session)
