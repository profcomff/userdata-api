from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.models.db import Category, Param
from userdata_api.schemas.param import ParamGet, ParamPatch, ParamPost
from userdata_api.utils.user import refreshing


param = APIRouter(prefix="/param", tags=["Param"])


@param.post("", response_model=ParamGet)
@refreshing
async def create_param(
    request: Request,
    param_inp: ParamPost,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userinfo.param.create"], allow_none=False, auto_error=True)),
) -> ParamGet:
    Category.get(param_inp.category_id, session=db.session)
    return ParamGet.from_orm(Param.create(session=db.session, **param_inp.dict()))


@param.get("/{id}", response_model=ParamGet)
async def get_param(id: int) -> ParamGet:
    return ParamGet.from_orm(Param.get(id, session=db.session))


@param.get("", response_model=list[ParamGet])
async def get_params() -> list[ParamGet]:
    return parse_obj_as(list[ParamGet], Param.query(session=db.session).all())


@param.patch("/{id}", response_model=ParamGet)
@refreshing
async def patch_param(
    request: Request,
    id: int,
    param_inp: ParamPatch,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userinfo.param.update"], allow_none=False, auto_error=True)),
) -> ParamGet:
    if param_inp.category_id:
        Category.get(param_inp.category_id, session=db.session)
    return ParamGet.from_orm(Param.update(id, session=db.session, **param_inp.dict(exclude_unset=True)))


@param.delete("/{id}")
@refreshing
async def delete_param(
    request: Request,
    id: int,
    _: dict[str, Any] = Depends(UnionAuth(scopes=["userinfo.param.delete"], allow_none=False, auto_error=True)),
) -> None:
    Param.delete(id, session=db.session)
