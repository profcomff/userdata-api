import pytest

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import *
from userdata_api.schemas.source import SourceGet
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated()
def test_create(client, dbsession):
    name = f"test{random_string()}"
    response = client.post("/source", json={"name": name, "trust_level": 12})
    assert response.status_code == 422
    response = client.post("/source", json={"name": name, "trust_level": 8})
    assert response.status_code == 200
    q = Source.get(response.json()["id"], session=dbsession)
    assert q
    assert response.json()["name"] == q.name == name
    assert response.json()["trust_level"] == q.trust_level == 8
    assert response.json()["id"] == q.id


@pytest.mark.authenticated()
def test_get(client, dbsession, source):
    _source = source()
    response = client.get(f"/source/{_source.id}")
    assert response.status_code == 200
    assert response.json()["name"] == _source.name
    assert response.json()["trust_level"] == _source.trust_level
    assert response.json()["id"] == _source.id


@pytest.mark.authenticated()
def test_get_all(client, dbsession, source):
    source1 = source()
    source2 = source()
    response = client.get(f"/source")
    assert response.status_code == 200
    assert SourceGet.from_orm(source1).dict() in response.json()
    assert SourceGet.from_orm(source2).dict() in response.json()


@pytest.mark.authenticated()
def test_update(client, dbsession, source):
    _source = source()
    response = client.patch(f"/source/{_source.id}", json={"name": f"{_source.name}updated", "trust_level": 7})
    assert response.status_code == 200
    assert response.json()["name"] == f"{_source.name}updated"
    assert response.json()["trust_level"] == 7
    dbsession.expire_all()
    q = Source.get(_source.id, session=dbsession)
    assert q
    assert response.json()["name"] == q.name
    assert response.json()["trust_level"] == q.trust_level
    assert response.json()["id"] == q.id


@pytest.mark.authenticated()
def test_delete(client, dbsession, source):
    _source = source()
    response = client.delete(f"/source/{_source.id}")
    assert response.status_code == 200
    response = client.get(f"/source/{_source.id}")
    assert response.status_code == 404
    with pytest.raises(ObjectNotFound):
        Source.get(_source.id, session=dbsession)
    assert Source.get(_source.id, with_deleted=True, session=dbsession)
