from sqlalchemy.orm import Session
from sqlalchemy.orm.collections import InstrumentedList

from userdata_api.models.db import Info, Param, Type
from userdata_api.schemas.user import user_interface


def most_trusted(infos: list[Info]) -> Info:
    _most_trusted: Info = infos[0]
    for info in infos:
        if info.source.trust_level > _most_trusted.source.trust_level:
            _most_trusted = info
    return _most_trusted


async def get_user_info(session: Session, user_id: int, scopes: list[str]) -> user_interface.User:
    infos: list[Info] = Info.query(session=session).filter(Info.owner_id == user_id).order_by(Info.modify_ts).all()
    param_dict: dict[Param, list[Info]] = {}
    for info in infos:
        info_scopes = (scope.name for scope in info.scopes)
        if not all(scope in scopes for scope in info_scopes):
            continue
        if info.param not in param_dict.keys():
            param_dict[info.param] = []
        param_dict[info.param].append(info)
    result = {}
    for param, v in param_dict.items():
        if param.category.name not in result.keys():
            result[param.category.name] = {}
        if param.type == Type.ALL:
            result[param.category.name][param.name] = v
        elif param.type == Type.LAST:
            result[param.category.name][param.name] = v[0]
        elif param.type == Type.MOST_TRUSTED:
            result[param.category.name][param.name] = most_trusted(v)
    return user_interface.User(**result)
