import datetime

import pytest
import sqlalchemy.exc

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import *
from userdata_api.schemas.info import InfoGet


def test_create(client, dbsession, param, source, random_string):
    _param = param()
    _source = source()
    name = f"test{random_string()}"
    response = client.post("/info", json={"owner_id": 0, "source_id": _source.id, "param_id": _param.id, "value": name})
    assert response.status_code == 200
    assert response.json()["value"] == name
    assert response.json()["source_id"] == _source.id
    assert response.json()["param_id"] == _param.id
    assert response.json()["owner_id"] == 0
    info = Info.get(response.json()["id"], session=dbsession)
    assert info
    assert response.json()["value"] == info.value
    assert response.json()["source_id"] == info.source_id
    assert response.json()["param_id"] == info.param_id
    assert response.json()["owner_id"] == info.owner_id
    dbsession.query(Info).filter(Info.id == response.json()["id"]).delete()


def test_get(client, dbsession, info):
    _info = info()
    response = client.get(f"/info/{_info.id}")
    assert response.status_code == 200
    assert response.json()["id"] == _info.id
    assert response.json()["owner_id"] == _info.owner_id
    assert response.json()["source_id"] == _info.source_id
    assert response.json()["param_id"] == _info.param_id
    assert response.json()["value"] == _info.value


def test_get_all(client, dbsession, info):
    info1 = info()
    info2 = info()
    response = client.get("/info")
    assert response.status_code == 200
    assert InfoGet.from_orm(info1).dict() in response.json()
    assert InfoGet.from_orm(info2).dict() in response.json()


def test_update(client, dbsession, info):
    _info = info()
    response = client.patch(f"/info/{_info.id}", json={"value": f"{_info.value}updated"})
    assert response.status_code == 200
    assert response.json()["value"] == f"{_info.value}updated"
    assert response.json()["param_id"] == _info.param_id
    assert response.json()["source_id"] == _info.source_id
    assert response.json()["owner_id"] == _info.owner_id
    q = Info.get(_info.id, session=dbsession)
    dbsession.expire_all()
    assert q
    assert response.json()["value"] == q.value
    assert response.json()["param_id"] == q.param_id
    assert response.json()["source_id"] == q.source_id
    assert response.json()["owner_id"] == q.owner_id


def test_delete(client, dbsession, info):
    _info = info()
    response = client.delete(f"/info/{_info.id}")
    assert response.status_code == 200
    with pytest.raises(ObjectNotFound):
        Info.get(_info.id, session=dbsession)
    q = Info.get(_info.id, session=dbsession, with_deleted=True)
    assert q
