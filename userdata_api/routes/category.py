from fastapi import APIRouter, Request
from fastapi_sqlalchemy import db
from pydantic import parse_obj_as

from userdata_api.models.db import Category, Scope
from userdata_api.schemas.category import CategoryGet, CategoryPatch, CategoryPost
from userdata_api.schemas.user import refreshing, user_interface


category = APIRouter(prefix="/category", tags=["Category"])


@category.post("", response_model=CategoryGet)
@refreshing
async def create_category(request: Request, category_inp: CategoryPost) -> CategoryGet:
    scopes = []
    category = Category.create(session=db.session, name=category_inp.name)
    for scope in category_inp.scopes:
        scopes.append(Scope.create(name=scope, category_id=category.id, session=db.session).name)
    return CategoryGet(id=category.id, name=category.name, scopes=scopes)


@category.get("/{id}", response_model=CategoryGet)
async def get_category(id: int) -> dict[str, str | int]:
    category = Category.get(id, session=db.session)
    return {"id": category.id, "name": category.name, "scopes": [_scope.name for _scope in category.scopes]}


@category.get("", response_model=list[CategoryGet])
async def get_categories() -> list[CategoryGet]:
    result: list[dict[str, str | int]] = []
    for category in Category.query(session=db.session).all():
        result.append({"id": category.id, "name": category.name, "scopes": [_scope.name for _scope in category.scopes]})
    return parse_obj_as(list[CategoryGet], result)


@category.patch("/{id}", response_model=CategoryGet)
@refreshing
async def patch_category(request: Request, id: int, category_inp: CategoryPatch) -> CategoryGet:
    category: Category = Category.get(id, session=db.session)
    scopes = set(category_inp.scopes)
    db_scopes = {_scope for _scope in category.scopes}
    to_create: set[str] = set()
    to_delete: set[Scope] = set()
    for scope in db_scopes:
        if scope.name not in scopes:
            to_delete.add(scope)
    for scope in scopes:
        if scope not in {_scope.name for _scope in db_scopes}:
            to_create.add(scope)
    for scope in to_create:
        Scope.create(name=scope, category_id=category.id, session=db.session)
    for scope in to_delete:
        db.session.delete(scope)
    db.session.flush()
    return CategoryGet.from_orm(Category.get(id, session=db.session))


@category.delete("/{id}")
@refreshing
async def delete_category(request: Request, id: int) -> None:
    category: Category = Category.get(id, session=db.session)
    for scope in category.scopes:
        db.session.delete(scope)
    Category.delete(id, session=db.session)
    return None
