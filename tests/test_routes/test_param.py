import pytest

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import *
from userdata_api.schemas.param import ParamGet
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("userdata.param.create")
def test_create_with_scopes(_client, dbsession, category):
    _category = category()
    name = f"test{random_string()}"
    response = _client.post(
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


@pytest.mark.authenticated("userdata.param.update")
def test_get(_client, dbsession, param):
    _param = param()
    response = _client.get(f"/param/{_param.id}")
    assert response.status_code == 200
    assert response.json()["name"] == _param.name
    assert response.json()["type"] == "last"
    assert response.json()["category_id"] == _param.category_id
    assert response.json()["changeable"] == _param.changeable
    assert response.json()["id"] == _param.id


@pytest.mark.authenticated("userdata.param.read")
def test_get_all(_client, dbsession, param):
    param1 = param()
    param2 = param()
    response = _client.get("/param")
    assert response.status_code == 200
    assert ParamGet.from_orm(param1).dict() in response.json()
    assert ParamGet.from_orm(param2).dict() in response.json()


@pytest.mark.authenticated("userdata.param.update")
def test_update(_client, dbsession, param):
    _param = param()
    response = _client.patch(f"/param/{_param.id}", json={"name": f"{_param.name}updated", "type": "all"})
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


@pytest.mark.authenticated("userdata.param.delete")
def test_delete(_client, dbsession, param):
    _param = param()
    response = _client.delete(f"/param/{_param.id}")
    assert response.status_code == 200
    with pytest.raises(ObjectNotFound):
        query1 = Param.get(_param.id, session=dbsession)
    query2 = Param.get(_param.id, with_deleted=True, session=dbsession)
    assert query2
