from __future__ import annotations

from userdata_api.schemas.admin import UserDebugCardGet, UserDebugCardUpdate


async def patch_user_info(
    new: UserDebugCardUpdate, user_id: int, user: dict[str, int | list[dict[str, str | int]]]
) -> None:
    """
    Обновить информацию о пользователе в соотетствии с переданным токеном.

    Метод обновляет только информацию из источников `admin`, `user` или `dwh`.

    Для обновления от имени админа нужен скоуп `userdata.info.admin`

    Для обновления информации из dwh нужен скоуп `userdata.info.dwh`

    :param new: модель запроса, в ней то, на что будет изменена информация о пользователе
    :param user_id: Айди пользователя
    :param user: Сессия пользователя выполняющего запрос
    :return: get_user_info для текущего пользователя с переданными правами
    """


async def get_user_info(user_id: int, user: dict[str, int | list[dict[str, str | int]]]) -> UserDebugCardGet:
    """
    Получить профсоюзную информацию пользователя для админки.

    :param user_id: Айди пользователя, информацию о котором запрашиваем
    :param user: Сессия пользователя, выполняющего запрос (должен иметь права администратора)
    :return: Словарь с данными пользователя:
        - user_id: ID пользователя
        - full_name: Полное имя (из параметра "Полное имя")
        - student_card_number: Номер студенческого билета (из параметра "Номер студенческого билета")
        - union_card_number: Номер профсоюзного билета (из параметра "Номер профсоюзного билета")
        - is_union_member: Статус мэтчинга (из параметра "Членство в профсоюзе")
        - last_check_timestamp: Дата последней проверки
    """
