from sqlalchemy.orm import Session
from sqlalchemy.orm.collections import InstrumentedList

from userdata_api.models.db import Info, Param, Source, Type
from userdata_api.schemas.user import user_interface


async def get_user_info(session: Session, user_id: int, scopes: list[dict[str, str | int]]) -> dict:
    infos: list[Info] = Info.query(session=session).filter(Info.owner_id == user_id).all()
    param_dict: dict[Param, list[Info]] = {}
    scope_names = [scope["name"] for scope in scopes]
    for info in infos:
        info_scopes = [scope.name for scope in info.scopes]
        if not all(scope in scope_names for scope in info_scopes):
            continue
        if info.param not in param_dict.keys():
            param_dict[info.param] = []
        param_dict[info.param].append(info)
    result = {}
    for param, v in param_dict.items():
        if param.category.name not in result.keys():
            result[param.category.name] = {}
        if param.type == Type.ALL:
            result[param.category.name][param.name] = [_v.value for _v in v]
        elif param.type == Type.LAST:
            q: Info = (
                Info.query(session=session)
                .filter(Info.owner_id == user_id, Info.param_id == param.id)
                .order_by(Info.modify_ts.desc())
                .first()
            )
            result[param.category.name][param.name] = q.value
        elif param.type == Type.MOST_TRUSTED:
            q: Info = (
                Info.query(session=session)
                .join(Source)
                .filter(Info.owner_id == user_id, Info.param_id == param.id)
                .order_by(Source.trust_level.desc())
                .order_by(Info.modify_ts.desc())
                .first()
            )
            result[param.category.name][param.name] = q.value
    return result
