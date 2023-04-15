import datetime

from userdata_api.models.db import *
from userdata_api.schemas.category import CategoryGet
from userdata_api.utils.utils import random_string


def test_create_with_scopes(client, dbsession):
    name = f"test{random_string()}"
    name2 = f"test.{random_string()}"
    name3 = f"test.{random_string()}.test"
    response = client.post("/category", json={"name": name, "scopes": [name2, name3]})
    assert response.status_code == 200
    category = dbsession.query(Category).filter(Category.name == name).one()
    assert category.name == name
    assert category.scopes
    assert [scope.name for scope in category.scopes] == [name2, name3]
    dbsession.query(Scope).filter(Scope.category_id == category.id).delete()
    dbsession.flush()
    dbsession.delete(category)
    dbsession.commit()


def test_create_with_no_scopes(client, dbsession):
    time = datetime.utcnow()
    response = client.post("/category", json={"name": f"test{time}", "scopes": []})
    assert response.status_code == 200
    category = dbsession.query(Category).filter(Category.name == f"test{time}").one()
    assert category.name == f"test{time}"
    assert not category.scopes
    dbsession.delete(category)
    dbsession.commit()


def test_get(client, dbsession, category):
    _category = category()
    response = client.get(f"/category/{_category.id}")
    assert response.status_code == 200
    assert response.json()["id"] == _category.id
    assert response.json()["scopes"] == [scope.name for scope in _category.scopes]
    assert response.json()["name"] == _category.name


def test_get_all(client, dbsession, category):
    category1 = category()
    category2 = category()
    response = client.get(f"/category")
    assert response.status_code == 200
    assert {
        "id": category1.id,
        "name": category1.name,
        "scopes": [scope.name for scope in category1.scopes],
    } in response.json()
    assert {
        "id": category2.id,
        "name": category2.name,
        "scopes": [scope.name for scope in category2.scopes],
    } in response.json()


def test_update(client, dbsession, category):
    _category = category()
    old_name = _category.name
    scopes = [scope.name for scope in _category.scopes]
    scopes.append("updated")
    response = client.patch(
        f"/category/{_category.id}",
        json={
            "name": f"{_category.name}updated",
            "scopes": scopes,
        },
    )
    assert response.status_code == 200
    id = _category.id
    dbsession.expire_all()
    assert _category.name == f"{old_name}updated"
    assert len(_category.scopes) == 3
    assert [scope.name for scope in _category.scopes] == scopes


def test_delete(client, dbsession, category):
    _category = category()
    response = client.delete(f"/category/{_category.id}")
    assert response.status_code == 200
    _cat_upd: Category = Category.query(session=dbsession).filter(Category.id == _category.id).one_or_none()
    assert not _cat_upd
    _cat_upd: Category = (
        Category.query(session=dbsession, with_deleted=True).filter(Category.id == _category.id).one_or_none()
    )
    assert _cat_upd
    response = client.get(f"/category/{_category.id}")
    assert response.status_code == 404
