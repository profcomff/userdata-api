import pytest

from userdata_api.models.db import ParamAlias
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("userdata.param.create")
def test_create_param_alias(client, dbsession, param, source):
    _param = param()
    _source = source()
    alias_name = f"alias_{random_string()}"
    response = client.post(
        f"/param/{_param.id}/alias",
        json={"name": alias_name, "source_id": _source.id},
    )
    assert response.status_code == 200
    assert response.json()["name"] == alias_name
    assert response.json()["param_id"] == _param.id
    assert response.json()["source_id"] == _source.id
    assert response.json()["source_name"] == _source.name
    alias = ParamAlias.get(response.json()["id"], session=dbsession)
    assert alias
    assert alias.name == alias_name
    dbsession.delete(alias)
    dbsession.commit()


@pytest.mark.authenticated("userdata.param.create")
def test_create_param_alias_global(client, dbsession, param):
    _param = param()
    alias_name = f"alias_{random_string()}"
    response = client.post(
        f"/param/{_param.id}/alias",
        json={"name": alias_name},
    )
    assert response.status_code == 200
    assert response.json()["name"] == alias_name
    assert response.json()["param_id"] == _param.id
    assert response.json()["source_id"] is None
    assert response.json()["source_name"] is None
    alias = ParamAlias.get(response.json()["id"], session=dbsession)
    dbsession.delete(alias)
    dbsession.commit()


@pytest.mark.authenticated("userdata.param.create")
def test_create_param_alias_unique_whole_table(client, dbsession, param):
    _param1 = param()
    _param2 = param()
    alias_name = f"alias_{random_string()}"
    response_1 = client.post(
        f"/param/{_param1.id}/alias",
        json={"name": alias_name},
    )
    assert response_1.status_code == 200
    response_2 = client.post(
        f"/param/{_param2.id}/alias",
        json={"name": alias_name},
    )
    assert response_2.status_code == 409
    alias = ParamAlias.get(response_1.json()["id"], session=dbsession)
    dbsession.delete(alias)
    dbsession.commit()


@pytest.mark.authenticated("userdata.param.create")
def test_get_param_aliases(client, dbsession, param, source):
    _param = param()
    _source = source()
    first_name = f"alias_{random_string()}"
    second_name = f"alias_{random_string()}"
    create_1 = client.post(
        f"/param/{_param.id}/alias",
        json={"name": first_name, "source_id": _source.id},
    )
    create_2 = client.post(
        f"/param/{_param.id}/alias",
        json={"name": second_name},
    )
    assert create_1.status_code == 200
    assert create_2.status_code == 200
    response = client.get(f"/param/{_param.id}/alias")
    assert response.status_code == 200
    assert any(item["name"] == first_name and item["source_id"] == _source.id for item in response.json())
    assert any(item["name"] == second_name and item["source_id"] is None for item in response.json())
    dbsession.delete(ParamAlias.get(create_1.json()["id"], session=dbsession))
    dbsession.delete(ParamAlias.get(create_2.json()["id"], session=dbsession))
    dbsession.commit()


@pytest.mark.authenticated("userdata.param.create", "userdata.param.update")
def test_patch_param_alias(client, dbsession, param, source):
    _param = param()
    _source = source()
    _new_source = source()
    alias_name = f"alias_{random_string()}"
    alias_new_name = f"alias_{random_string()}"
    create = client.post(
        f"/param/{_param.id}/alias",
        json={"name": alias_name, "source_id": _source.id},
    )
    assert create.status_code == 200
    alias_id = create.json()["id"]
    response = client.patch(
        f"/param/{_param.id}/alias/{alias_id}",
        json={"name": alias_new_name, "source_id": _new_source.id},
    )
    assert response.status_code == 200
    assert response.json()["name"] == alias_new_name
    assert response.json()["source_id"] == _new_source.id
    dbsession.expire_all()
    alias = ParamAlias.get(alias_id, session=dbsession)
    assert alias.name == alias_new_name
    assert alias.source_id == _new_source.id
    dbsession.delete(alias)
    dbsession.commit()


@pytest.mark.authenticated("userdata.param.create", "userdata.param.delete")
def test_delete_param_alias(client, dbsession, param):
    _param = param()
    alias_name = f"alias_{random_string()}"
    create = client.post(
        f"/param/{_param.id}/alias",
        json={"name": alias_name},
    )
    assert create.status_code == 200
    alias_id = create.json()["id"]
    response = client.delete(f"/param/{_param.id}/alias/{alias_id}")
    assert response.status_code == 200
    alias = ParamAlias.get(alias_id, session=dbsession, with_deleted=True)
    assert alias.is_deleted is True
    dbsession.delete(alias)
    dbsession.commit()
