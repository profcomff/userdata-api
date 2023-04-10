from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.models.db import Info, Param, Source
from userdata_api.schemas.info import InfoGet, InfoPatch, InfoPost


info = APIRouter(prefix="/info", tags=["Info"])


@info.post("", response_model=InfoGet)
async def create_info(
    info_inp: InfoPost, user: dict[str, str] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True))
) -> InfoGet:
    if "userinfo.info.create" not in user["session_scopes"] and user["user_id"] != info_inp.owner_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    Source.get(info_inp.source_id, session=db.session)
    Param.get(info_inp.param_id, session=db.session)
    return InfoGet.from_orm(Info.create(session=db.session, **info_inp.dict()))


@info.get("/{id}", response_model=InfoGet)
async def get_info(
    id: int, user: dict[str, str] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True))
) -> InfoGet:
    info = Info.get(id, session=db.session)
    if "userinfo.info.read" not in user["session_scopes"] and user["user_id"] != info.owner_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return InfoGet.from_orm(info)


@info.get("", response_model=list[InfoGet])
async def get_infos(
    _: dict[str, str] = Depends(UnionAuth(scopes=["userinfo.info.read"], allow_none=False, auto_error=True))
) -> list[InfoGet]:
    return parse_obj_as(list[InfoGet], Info.query(session=db.session).all())


@info.patch("/{id}", response_model=InfoGet)
async def patch_info(
    id: int,
    info_inp: InfoPatch,
    user: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True)),
) -> InfoGet:
    if info_inp.param_id:
        Param.get(info_inp.param_id, session=db.session)
    if info_inp.source_id:
        Source.get(info_inp.source_id, session=db.session)
    info = Info.get(id, session=db.session)
    if "userinfo.info.update" not in user["session_scopes"] and user["user_id"] != info.owner_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return InfoGet.from_orm(Info.update(id, session=db.session, **info_inp.dict(exclude_unset=True)))


@info.delete("/{id}")
async def delete_info(
    id: int, user: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True))
) -> None:
    info = Info.get(id, session=db.session)
    if "userinfo.info.delete" not in user["session_scopes"] and user["user_id"] != info.owner_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    Info.delete(id, session=db.session)
