import json
from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from starlette.responses import Response

from userdata_api.schemas.user import user_interface
from userdata_api.utils.user import get_user_info as get_user_info_func


user = APIRouter(prefix="/user", tags=["User"])


@user.get("/{id}", response_model=user_interface.User)
async def get_user_info(
    id: int, user: dict[str, Any] = Depends(UnionAuth(scopes=[], allow_none=False, auto_error=True))
):
    if "userinfo.user.read" not in tuple(scope["name"] for scope in user["session_scopes"]) and user["user_id"] != id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await user_interface.refresh(db.session)
    res = await get_user_info_func(db.session, id, user["session_scopes"])
    user_interface.User(**res)
    return Response(content=json.dumps(res), media_type="application/json")
