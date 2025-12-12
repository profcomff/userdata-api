from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends

from userdata_api.schemas.admin import UserCardGet, UserCardUpdate
from userdata_api.schemas.response_model import StatusResponseModel
from userdata_api.utils.admin import get_user_info
from userdata_api.utils.admin import patch_user_info


admin = APIRouter(prefix="/admin", tags=["Admin"])


@admin.get("/user/{user_id}", response_model=UserCardGet)
async def get_user_card(
    user_id: int,
    user: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.info.admin"], allow_none=False, auto_error=True)),
) -> UserCardGet:
    """
    Получает профсоюзную информацию пользователя.

    Скоупы: `["userdata.info.admin"]`
    """

    return UserCardGet.model_validate(await get_user_info(user_id, user))


@admin.patch("/user/{user_id}", response_model=StatusResponseModel)
async def update_user_card(
    new_info: UserCardUpdate,
    user_id: int,
    user: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.info.admin"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Обновить данные в профсоюзной информации пользователя.

    Скоупы: `["userdata.info.admin"]`

     - **user_id**: id пользователя.
    """

    await patch_user_info(new_info, user_id, user)
    return StatusResponseModel(status="Success", message="User patch succeeded", ru="Изменение успешно")
