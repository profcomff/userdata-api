from fastapi import APIRouter
from fastapi_sqlalchemy import db

from userdata_api.schemas.user import user_interface
from userdata_api.utils.user import get_user_info as get_user_info_func


user = APIRouter(prefix="/user", tags=["User"])


@user.get("/{id}", response_model=user_interface.User)
async def get_user_info(id: int):
    return get_user_info_func(db.session, id, [])
