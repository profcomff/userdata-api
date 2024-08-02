from time import sleep

import pytest

from userdata_api.models.db import *
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("test.scope", user_id=0)
def test_get(client, dbsession, source, info_no_scopes):
    info1: Info = info_no_scopes()
    info1.category.read_scope = "test.scope"
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert info1.category.name == response.json()["items"][0]["category"]
    assert info1.param.name == response.json()["items"][0]["param"]
    assert info1.value == response.json()["items"][0]["value"]


@pytest.mark.authenticated(user_id=1)
def test_get_no_all_scopes(client, dbsession, source, info_no_scopes):
    info1: Info = info_no_scopes()
    info1.category.read_scope = "test.scope"
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert info1.category.name not in response.json()
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated()
def test_get_a_few(client, dbsession, category_no_scopes, source):
    source = source()
    category1 = category_no_scopes()
    category2 = category_no_scopes()
    category3 = category_no_scopes()
    param1 = Param(
        name=f"test{random_string()}", category_id=category1.id, type="last", changeable=True, is_required=True
    )
    param2 = Param(
        name=f"test{random_string()}", category_id=category1.id, type="last", changeable=True, is_required=True
    )
    param3 = Param(
        name=f"test{random_string()}", category_id=category2.id, type="last", changeable=True, is_required=True
    )
    param4 = Param(
        name=f"test{random_string()}", category_id=category3.id, type="last", changeable=True, is_required=True
    )
    dbsession.add_all([param1, param2, param3, param4])
    dbsession.flush()
    info1 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param2.id, owner_id=0)
    info3 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param3.id, owner_id=0)
    info4 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param4.id, owner_id=0)
    dbsession.add_all([info1, info2, info3, info4])
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert {"category": category1.name, "param": info1.param.name, "value": info1.value} in list(
        response.json()["items"]
    )
    assert {"category": category1.name, "param": info2.param.name, "value": info2.value} in list(
        response.json()["items"]
    )
    assert {"category": category2.name, "param": info3.param.name, "value": info3.value} in list(
        response.json()["items"]
    )
    assert {"category": category3.name, "param": info4.param.name, "value": info4.value} in list(
        response.json()["items"]
    )
    assert len(list(response.json()["items"])) == 4
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.delete(info4)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.delete(param2)
    dbsession.delete(param3)
    dbsession.delete(param4)
    dbsession.delete(category1)
    dbsession.delete(category2)
    dbsession.delete(category3)
    dbsession.commit()


@pytest.mark.authenticated()
def test_get_a_few_with_trust_level(client, dbsession, category_no_scopes, source):
    source1 = source()
    source2 = source()
    category1 = category_no_scopes()
    category2 = category_no_scopes()
    category3 = category_no_scopes()
    param1 = Param(
        name=f"test{random_string()}", category_id=category1.id, type="all", changeable=True, is_required=True
    )
    param2 = Param(
        name=f"test{random_string()}", category_id=category1.id, type="all", changeable=True, is_required=True
    )
    param3 = Param(
        name=f"test{random_string()}", category_id=category2.id, type="last", changeable=True, is_required=True
    )
    param4 = Param(
        name=f"test{random_string()}", category_id=category3.id, type="most_trusted", changeable=True, is_required=True
    )
    dbsession.add_all([param1, param2, param3, param4])
    dbsession.flush()
    source2.trust_level = 9
    dbsession.commit()

    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param1.id, owner_id=0)
    info3 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)

    info4 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param2.id, owner_id=0)

    info5 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param3.id, owner_id=0)
    info6 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param3.id, owner_id=0)
    dbsession.add_all([info1, info2, info3, info4, info5, info6])
    dbsession.commit()
    info7 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param3.id, owner_id=0)

    info8 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param4.id, owner_id=0)
    info9 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param4.id, owner_id=0)
    info10 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param4.id, owner_id=0)
    dbsession.add_all([info7, info8, info9, info10])
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert {"category": category1.name, "param": param1.name, "value": info1.value} in list(response.json()["items"])
    assert {"category": category1.name, "param": param1.name, "value": info2.value} in list(response.json()["items"])
    assert {"category": category1.name, "param": param1.name, "value": info3.value} in list(response.json()["items"])
    assert {"category": category1.name, "param": param2.name, "value": info4.value} in list(response.json()["items"])
    assert {"category": category2.name, "param": param3.name, "value": info7.value} in list(response.json()["items"])
    assert {"category": category3.name, "param": param4.name, "value": info9.value} in list(response.json()["items"])
    assert len(response.json()["items"]) == 6
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.delete(info4)
    dbsession.delete(info5)
    dbsession.delete(info6)
    dbsession.delete(info7)
    dbsession.delete(info8)
    dbsession.delete(info9)
    dbsession.delete(info10)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.delete(param2)
    dbsession.delete(param3)
    dbsession.delete(param4)
    dbsession.delete(category1)
    dbsession.delete(category2)
    dbsession.delete(category3)
    dbsession.commit()


@pytest.mark.authenticated()
def test_get_last_most_trusted(client, dbsession, category_no_scopes, source):
    source1 = source()
    source2 = source()
    category1 = category_no_scopes()
    param1 = Param(
        name=f"test{random_string()}", category_id=category1.id, type="most_trusted", changeable=True, is_required=True
    )
    dbsession.add(param1)
    dbsession.flush()
    source2.trust_level = 9
    dbsession.commit()
    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param1.id, owner_id=0)
    dbsession.add_all([info1, info2])
    dbsession.commit()
    sleep(0.1)
    info3 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info4 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param1.id, owner_id=0)
    dbsession.add_all([info3, info4])
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert {"category": category1.name, "param": param1.name, "value": info4.value} in list(response.json()["items"])
    assert len(response.json()["items"]) == 1
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.delete(info4)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.delete(category1)
    dbsession.commit()
