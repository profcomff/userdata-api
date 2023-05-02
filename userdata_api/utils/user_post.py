from fastapi_sqlalchemy import db

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import Category, Info, Param, Source
from userdata_api.utils.exception_process import __get_process_exception


async def __param(user_id: int, category: Category, param_name: str, values: list[dict[str, str | int]]) -> None:
    param_id = (
        db.session.query(Param.id)
        .join(Category)
        .filter(Param.name == param_name)
        .filter(Category.id == category.id)
        .one_or_none()
    )[0]
    for info in db.session.query(Info).filter(Info.owner_id == user_id, Info.param_id == param_id).all():
        Info.delete(info.id, session=db.session)
    sources = Source.query(session=db.session).filter(Source.name.in_([value.get("source") for value in values])).all()
    assert len(sources) == len(frozenset([value.get("source") for value in values]))
    source_dict: dict[str, Source] = {}
    for source in sources:
        source_dict[source.name] = source
    for value in values:
        Info.create(
            session=db.session,
            owner_id=user_id,
            param_id=param_id,
            source_id=source_dict[value["source"]].id,
            value=value["value"],
        )


async def __category(user_id: int, category: Category, category_dict: dict[str, list[dict[str, str | int]]]):
    for k, v in category_dict.items():
        param = Param.query(session=db.session).filter(Param.name == k, Param.category_id == category.id).one_or_none()
        if not param:
            db.session.rollback()
            raise ObjectNotFound(Param, k)
        await __param(user_id, category, k, v)


async def process_post_model(
    user_id: int,
    model: dict[str, dict[str, list[dict[str, str | int]]] | int],
    user: dict[str, int | list[dict[str, str | int]]],
):
    scope_names = [scope["name"] for scope in user["session_scopes"]]
    for k, v in model.items():
        category = Category.query(session=db.session).filter(Category.name == k).one_or_none()
        if _exc := __get_process_exception(category, k, scope_names):
            db.session.rollback()
            raise _exc
        else:
            await __category(user_id, category, v)
