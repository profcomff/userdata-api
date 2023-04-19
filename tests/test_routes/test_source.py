import pytest

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import *
from userdata_api.schemas.source import SourceGet
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("userdata.source.create")
def test_create(_client, dbsession):
    name = f"test{random_string()}"
    response = _client.post("/source", json={"name": name, "trust_level": 12})
    assert response.status_code == 422
    response = _client.post("/source", json={"name": name, "trust_level": 8})
    assert response.status_code == 200
    q = Source.get(response.json()["id"], session=dbsession)
    assert q
    assert response.json()["name"] == q.name == name
    assert response.json()["trust_level"] == q.trust_level == 8
    assert response.json()["id"] == q.id


@pytest.mark.authenticated("userdata.source.read")
def test_get(_client, dbsession, source):
    _source = source()
    response = _client.get(f"/source/{_source.id}")
    assert response.status_code == 200
    assert response.json()["name"] == _source.name
    assert response.json()["trust_level"] == _source.trust_level
    assert response.json()["id"] == _source.id


@pytest.mark.authenticated("userdata.source.read")
def test_get_all(_client, dbsession, source):
    source1 = source()
    source2 = source()
    response = _client.get(f"/source")
    assert response.status_code == 200
    assert SourceGet.from_orm(source1).dict() in response.json()
    assert SourceGet.from_orm(source2).dict() in response.json()


@pytest.mark.authenticated("userdata.source.update")
def test_update(_client, dbsession, source):
    _source = source()
    response = _client.patch(f"/source/{_source.id}", json={"name": f"{_source.name}updated", "trust_level": 7})
    assert response.status_code == 200
    assert response.json()["name"] == f"{_source.name}updated"
    assert response.json()["trust_level"] == 7
    dbsession.expire_all()
    q = Source.get(_source.id, session=dbsession)
    assert q
    assert response.json()["name"] == q.name
    assert response.json()["trust_level"] == q.trust_level
    assert response.json()["id"] == q.id


@pytest.mark.authenticated("userdata.source.delete")
def test_delete(_client, dbsession, source):
    _source = source()
    response = _client.delete(f"/source/{_source.id}")
    assert response.status_code == 200
    response = _client.get(f"/source/{_source.id}")
    assert response.status_code == 404
    with pytest.raises(ObjectNotFound):
        Source.get(_source.id, session=dbsession)
    assert Source.get(_source.id, with_deleted=True, session=dbsession)
