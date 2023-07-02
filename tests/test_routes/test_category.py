import datetime

import pytest

from userdata_api.models.db import *
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("userdata.category.create")
def test_create_with_scopes(client, dbsession):
    name = f"test{random_string()}"
    name2 = f"test.{random_string()}"
    name3 = f"test.{random_string()}.test"
    response = client.post("/category", json={"name": name, "read_scope": name2, "update_scope": name3})
    assert response.status_code == 200
    category = dbsession.query(Category).filter(Category.name == name).one()
    assert category.name == name
    assert category.update_scope == name3
    assert category.read_scope == name2
    dbsession.delete(category)
    dbsession.commit()


@pytest.mark.authenticated("userdata.category.create")
def test_create_with_no_scopes(client, dbsession):
    time = datetime.utcnow()
    response = client.post(
        "/category",
        json={
            "name": f"test{time}",
        },
    )
    assert response.status_code == 200
    category = dbsession.query(Category).filter(Category.name == f"test{time}").one()
    assert category.name == f"test{time}"
    assert not category.read_scope and not category.update_scope
    dbsession.delete(category)
    dbsession.commit()


@pytest.mark.authenticated("userdata.category.read")
def test_get(client, dbsession, category):
    _category = category()
    response = client.get(f"/category/{_category.id}")
    assert response.status_code == 200
    assert response.json()["id"] == _category.id
    assert response.json()["read_scope"] == _category.read_scope
    assert response.json()["update_scope"] == _category.update_scope
    assert response.json()["name"] == _category.name


@pytest.mark.authenticated("userdata.category.read")
def test_get_all(client, dbsession, category):
    category1 = category()
    category2 = category()
    category1.dict()
    response = client.get(f"/category")
    assert response.status_code == 200
    assert {
        "id": category1.id,
        "name": category1.name,
        "read_scope": category1.read_scope,
        "update_scope": category1.update_scope,
    } in response.json()
    assert {
        "id": category2.id,
        "name": category2.name,
        "read_scope": category2.read_scope,
        "update_scope": category2.update_scope,
    } in response.json()


@pytest.mark.authenticated("userdata.category.update")
def test_update(client, dbsession, category):
    _category = category()
    old_name = _category.name
    old_update_scope = _category.update_scope
    response = client.patch(
        f"/category/{_category.id}",
        json={
            "name": f"{_category.name}updated",
            "read_scope": "updated",
        },
    )
    assert response.status_code == 200
    dbsession.expire_all()
    assert _category.name == f"{old_name}updated"
    assert _category.read_scope == "updated"
    assert _category.update_scope == old_update_scope


@pytest.mark.authenticated("userdata.category.delete", "userdata.category.read")
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
