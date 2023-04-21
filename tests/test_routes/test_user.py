import datetime
from time import sleep

import pytest
import sqlalchemy.exc

from userdata_api.exceptions import ObjectNotFound
from userdata_api.models.db import *
from userdata_api.schemas.source import SourceGet
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated(
    "it.needs.by.test.user.get.first", "it.needs.by.test.user.get.second", "it.needs.by.test.user.get.third"
)
def test_get(client, dbsession, source, info_no_scopes):
    info1: Info = info_no_scopes()
    scope1 = Scope(name="it.needs.by.test.user.get.first", category_id=info1.category.id)
    scope2 = Scope(name="it.needs.by.test.user.get.second", category_id=info1.category.id)
    scope3 = Scope(name="it.needs.by.test.user.get.third", category_id=info1.category.id)
    dbsession.add_all([scope1, scope3, scope2])
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert info1.category.name in response.json().keys()
    assert response.json()[info1.category.name] == {info1.param.name: info1.value}
    dbsession.delete(scope1)
    dbsession.delete(scope2)
    dbsession.delete(scope3)
    dbsession.commit()


@pytest.mark.authenticated(
    "it.needs.by.test.user.get.first", "it.needs.by.test.user.get.second", "it.needs.by.test.user.get.third"
)
def test_get_no_all_scopes(client, dbsession, source, info_no_scopes):
    info1: Info = info_no_scopes()
    scope1 = Scope(name="it.needs.by.test.user.get.first", category_id=info1.category.id)
    scope2 = Scope(name="it.needs.by.test.user.get.second", category_id=info1.category.id)
    scope3 = Scope(name="it.needs.by.test.user.get.third", category_id=info1.category.id)
    scope4 = Scope(name="it.needs.by.test.user.get.fourth", category_id=info1.category.id)
    dbsession.add_all([scope1, scope2, scope3, scope4])
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert info1.category.name not in response.json()
    dbsession.delete(scope1)
    dbsession.delete(scope2)
    dbsession.delete(scope3)
    dbsession.delete(scope4)
    dbsession.commit()


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
    assert response.json().keys() == [category1.name, category2.name, category3.name]
    assert response.json()[category1.name] == {info1.param.name: info1.value, info2.param.name: info2.value}
    assert response.json()[category2.name] == {info3.param.name: info3.value}
    assert response.json()[category3.name] == {info4.param.name: info4.value}
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.delete(info4)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.delete(param2)
    dbsession.delete(param3)
    dbsession.delete(param4)
    dbsession.commit()


@pytest.mark.authenticated()
def test_get_a_few(client, dbsession, category_no_scopes, source):
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
    sleep(0.1)
    info7 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param3.id, owner_id=0)

    info8 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param4.id, owner_id=0)
    info9 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param4.id, owner_id=0)
    info10 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param4.id, owner_id=0)
    dbsession.add_all([info7, info8, info9, info10])
    dbsession.commit()
    response = client.get(f"/user/{info1.owner_id}")
    assert response.status_code == 200
    assert set(response.json()[category1.name][param1.name]) == {info2.value, info3.value, info1.value}
    assert set(response.json()[category1.name][param2.name]) == {info4.value}
    assert response.json()[category2.name] == {param3.name: info7.value}
    assert response.json()[category3.name] == {param4.name: info9.value}
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
    assert category1.name in response.json().keys()
    assert response.json()[category1.name] == {param1.name: info4.value}
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(info3)
    dbsession.delete(info4)
    dbsession.flush()
    dbsession.delete(param1)
    dbsession.commit()
