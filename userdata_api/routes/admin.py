from typing import Any

from auth_lib.fastapi import UnionAuth
from fastapi import APIRouter, Depends

from userdata_api.schemas.admin import UserDebugCardGet, UserDebugCardUpdate
from userdata_api.schemas.response_model import StatusResponseModel
from userdata_api.utils.admin import get_user_info as get
from userdata_api.utils.admin import patch_user_info as patch


admin = APIRouter(prefix="/admin", tags=["Admin"])


@admin.get("/user/{user_id}", response_model=UserDebugCardGet)
async def get_user_debug_card(
    user_id: int,
    user: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.info.admin"], allow_none=False, auto_error=True)),
) -> UserDebugCardGet:
    """
    Получает профсоюзную информацию пользователя.

    Скоупы: `["userdata.info.admin"]`
    """

    return UserDebugCardGet.model_validate(await get(user_id, user))


@admin.patch("/user/{user_id}", response_model=StatusResponseModel)
async def update_user_debug_card(
    new_info: UserDebugCardUpdate,
    user_id: int,
    user: dict[str, Any] = Depends(UnionAuth(scopes=["userdata.info.admin"], allow_none=False, auto_error=True)),
) -> StatusResponseModel:
    """
    Обновить данные в профсоюзной информации пользователя.

    Скоупы: `["userdata.info.admin"]`

     - **user_id**: id пользователя.

    Возвращает **ObjectNotFound** пользователь с указанным user_id не найден.
    """

    await patch(new_info, user_id, user)
    return StatusResponseModel(status="Success", message="User patch succeeded", ru="Изменение успешно")
