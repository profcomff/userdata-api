from time import sleep

import pytest

from userdata_api.models.db import Info, Param
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("userdata.info.admin")
def test_get(client, dbsession, category_no_scopes, source):
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
    info2 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param2.id, owner_id=1)
    info3 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param3.id, owner_id=0)
    info4 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param4.id, owner_id=1)
    dbsession.add_all([info1, info2, info3, info4])
    dbsession.commit()
    response = client.get(f"/user", params={"users": [0, 1], "categories": [category1.id, category2.id, category3.id]})
    assert response.status_code == 200
    assert {"user_id": 1, "category": category1.name, "param": info2.param.name, "value": info2.value} in list(
        response.json()["items"]
    )
    assert {"user_id": 1, "category": category3.name, "param": info4.param.name, "value": info4.value} in list(
        response.json()["items"]
    )
    assert {"user_id": 0, "category": category1.name, "param": info1.param.name, "value": info1.value} in list(
        response.json()["items"]
    )
    assert {"user_id": 0, "category": category2.name, "param": info3.param.name, "value": info3.value} in list(
        response.json()["items"]
    )
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.delete(info4)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.delete(param2)
    dbsession.delete(param3)
    dbsession.delete(param4)
    dbsession.flush()
    dbsession.delete(category1)
    dbsession.delete(category2)
    dbsession.delete(category3)
    dbsession.commit()


@pytest.mark.authenticated("userdata.info.admin")
def test_get_some_users(client, dbsession, category_no_scopes, source):
    source = source()
    category1 = category_no_scopes()
    param1 = Param(
        name=f"test{random_string()}", category_id=category1.id, type="last", changeable=True, is_required=True
    )
    dbsession.add_all([param1])
    dbsession.flush()
    info1 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=1)
    info2 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=2)
    info3 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=3)
    dbsession.add_all([info1, info2, info3])
    dbsession.commit()
    response = client.get(f"/user", params={"users": [1, 2], "categories": [category1.id]})
    print(client.get(f"/user", params={"users": [2], "categories": [category1.id]}).json())
    print(client.get(f"/user", params={"users": [1], "categories": [category1.id]}).json())
    print(client.get(f"/user", params={"users": [1, 2], "categories": [category1.id]}).json())
    print(client.get(f"/user", params={"users": [2, 1], "categories": [category1.id]}).json())
    assert response.status_code == 200
    print(response.json())
    assert {"user_id": 1, "category": category1.name, "param": param1.name, "value": info1.value} in list(
        response.json()["items"]
    )
    assert {"user_id": 2, "category": category1.name, "param": param1.name, "value": info2.value} in list(
        response.json()["items"]
    )
    assert {"user_id": 3, "category": category1.name, "param": param1.name, "value": info3.value} not in list(
        response.json()["items"]
    )
    response = client.get(f"/user", params={"users": [3], "categories": [category1.id]})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert {"user_id": 3, "category": category1.name, "param": param1.name, "value": info3.value} in list(
        response.json()["items"]
    )
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.flush()
    dbsession.delete(category1)
    dbsession.commit()


@pytest.mark.authenticated("userdata.info.admin")
def test_get_some_categories(client, dbsession, category_no_scopes, source):
    source = source()
    category1 = category_no_scopes()
    category2 = category_no_scopes()
    category3 = category_no_scopes()
    param1 = Param(
        name=f"test{random_string()}", category_id=category1.id, type="last", changeable=True, is_required=True
    )
    param2 = Param(
        name=f"test{random_string()}", category_id=category2.id, type="last", changeable=True, is_required=True
    )
    param3 = Param(
        name=f"test{random_string()}", category_id=category3.id, type="last", changeable=True, is_required=True
    )
    dbsession.add_all([param1, param2, param3])
    dbsession.flush()
    info1 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=1)
    info2 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param2.id, owner_id=1)
    info3 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param3.id, owner_id=1)
    dbsession.add_all([info1, info2, info3])
    dbsession.commit()
    response = client.get(f"/user", params={"users": [1], "categories": [category1.id, category2.id]})
    assert response.status_code == 200
    assert {"user_id": 1, "category": category1.name, "param": info1.param.name, "value": info1.value} in list(
        response.json()["items"]
    )
    assert {"user_id": 1, "category": category2.name, "param": info2.param.name, "value": info2.value} in list(
        response.json()["items"]
    )
    assert {"user_id": 1, "category": category3.name, "param": info3.param.name, "value": info3.value} not in list(
        response.json()["items"]
    )

    response = client.get(f"/user", params={"users": [1], "categories": [category3.id]})
    assert {"user_id": 1, "category": category3.name, "param": info3.param.name, "value": info3.value} in list(
        response.json()["items"]
    )

    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.delete(param2)
    dbsession.delete(param3)
    dbsession.flush()
    dbsession.delete(category1)
    dbsession.delete(category2)
    dbsession.delete(category3)
    dbsession.commit()
