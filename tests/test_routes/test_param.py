import datetime

import pytest
import sqlalchemy.exc

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import *
from userdata_api.schemas.param import ParamGet
from userdata_api.utils.utils import random_string


def test_create_with_scopes(client, dbsession, category):
    _category = category()
    name = f"test{random_string()}"
    response = client.post(
        "/param",
        json={"name": name, "category_id": _category.id, "type": "last", "changeable": "true", "is_required": "true"},
    )
    assert response.status_code == 200
    assert response.json()["id"]
    assert response.json()["name"] == name
    assert response.json()["category_id"] == _category.id
    assert response.json()["type"] == "last"
    assert response.json()["changeable"] == True
    assert response.json()["is_required"] == True
    param = Param.get(response.json()["id"], session=dbsession)
    assert param
    assert param.name == name
    assert param.id == response.json()["id"]
    assert param.type == "last"
    assert param.changeable == True
    assert param.category_id == _category.id
    assert param.category == _category
    dbsession.delete(param)
    dbsession.flush()


def test_get(client, dbsession, param):
    _param = param()
    response = client.get(f"/param/{_param.id}")
    assert response.status_code == 200
    assert response.json()["name"] == _param.name
    assert response.json()["type"] == "last"
    assert response.json()["category_id"] == _param.category_id
    assert response.json()["changeable"] == _param.changeable
    assert response.json()["id"] == _param.id


def test_get_all(client, dbsession, param):
    param1 = param()
    param2 = param()
    response = client.get("/param")
    assert response.status_code == 200
    assert ParamGet.from_orm(param1).dict() in response.json()
    assert ParamGet.from_orm(param2).dict() in response.json()


def test_update(client, dbsession, param):
    _param = param()
    response = client.patch(f"/param/{_param.id}", json={"name": f"{_param.name}updated", "type": "all"})
    assert response.status_code == 200
    assert response.json()["name"] == f"{_param.name}updated"
    assert response.json()["type"] == "all"
    assert response.json()["changeable"] == _param.changeable
    assert response.json()["id"] == _param.id
    assert response.json()["category_id"] == _param.category_id
    dbsession.expire_all()
    q: Param = Param.get(_param.id, session=dbsession)
    assert q
    assert response.json()["name"] == q.name
    assert response.json()["type"] == q.type
    assert response.json()["changeable"] == q.changeable
    assert response.json()["id"] == q.id
    assert response.json()["category_id"] == q.category_id


def test_delete(client, dbsession, param):
    _param = param()
    response = client.delete(f"/param/{_param.id}")
    assert response.status_code == 200
    with pytest.raises(ObjectNotFound):
        query1 = Param.get(_param.id, session=dbsession)
    query2 = Param.get(_param.id, with_deleted=True, session=dbsession)
    assert query2
