import pytest

from userdata_api.models.db import *
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", user_id=1)
def test_main_scenario(dbsession, client, param, source):
    param1 = param()
    param2 = param()
    param3 = Param(
        name=f"test{random_string()}", category_id=param1.category_id, type="all", changeable=True, is_required=True
    )
    dbsession.add(param3)
    source1 = source()
    source2 = source()
    param1.category.update_scope = "test.cat_update.first"
    param2.category.update_scope = "test.cat_update.second"
    dbsession.flush()
    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param1.id, owner_id=0)
    dbsession.add_all([info1, info2])
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            param1.category.name: {
                param1.name: [
                    {"value": "first_updated", "source": source1.name},
                    {"value": "second_updated", "source": source1.name},
                ],
                param3.name: [{"value": "fourth_updated", "source": source2.name}],
            },
            param2.category.name: {
                param2.name: [{"value": "third_updated", "source": source1.name}],
            },
        },
    )
    assert response.status_code == 200
    assert info1.is_deleted
    assert info2.is_deleted
    first_param = [
        info.dict() for info in dbsession.query(Info).filter(Info.param_id == param1.id, Info.owner_id == 0).all()
    ]
    second_param = [
        info.dict() for info in dbsession.query(Info).filter(Info.param_id == param2.id, Info.owner_id == 0).all()
    ]
    third_param = [
        info.dict() for info in dbsession.query(Info).filter(Info.param_id == param3.id, Info.owner_id == 0).all()
    ]
    assert first_param and second_param and third_param
    for info in first_param:
        if info["value"] == "first_updated" and info["source_id"] == source1.id:
            break
    else:
        assert False
    for info in first_param:
        if info["value"] == "second_updated" and info["source_id"] == source1.id:
            break
    else:
        assert False
    for info in second_param:
        if info["value"] == "third_updated" and info["source_id"] == source1.id:
            break
    else:
        assert False
    for info in third_param:
        if info["value"] == "fourth_updated" and info["source_id"] == source2.id:
            break
    else:
        assert False
    for info in first_param:
        dbsession.query(Info).filter(Info.id == info["id"]).delete()
    for info in second_param:
        dbsession.query(Info).filter(Info.id == info["id"]).delete()
    for info in third_param:
        dbsession.query(Info).filter(Info.id == info["id"]).delete()
    dbsession.commit()
    dbsession.delete(param3)


@pytest.mark.authenticated(user_id=1)
def test_forbidden(dbsession, client, param, source):
    param1 = param()
    param2 = param()
    param3 = Param(
        name=f"test{random_string()}", category_id=param1.category_id, type="all", changeable=True, is_required=True
    )
    dbsession.add(param3)
    source1 = source()
    source2 = source()
    param1.category.update_scope = "test.cat_update.first"
    param2.category.update_scope = "test.cat_update.second"
    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param2.id, owner_id=0)
    dbsession.add_all([info1, info2])
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            param1.category.name: {
                param1.name: [
                    {"value": "first_updated", "source": source1.name},
                    {"value": "second_updated", "source": source1.name},
                ],
                param3.name: [{"value": "fourth_updated", "source": source2.name}],
            },
            param2.category.name: {
                param2.name: [{"value": "third_updated", "source": source1.name}],
            },
        },
    )
    dbsession.expire_all()
    assert response.status_code == 403
    assert not info1.is_deleted
    assert not info2.is_deleted
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(param3)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", user_id=1)
def test_category_not_found(dbsession, client, param, source):
    param1 = param()
    param2 = param()
    param3 = Param(
        name=f"test{random_string()}", category_id=param1.category_id, type="all", changeable=True, is_required=True
    )
    dbsession.add(param3)
    source1 = source()
    source2 = source()
    param1.category.update_scope = "test.cat_update.first"
    param2.category.update_scope = "test.cat_update.second"
    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param2.id, owner_id=0)
    dbsession.add_all([info1, info2])
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            f"{param1.category.name}404": {
                param1.name: [
                    {"value": "first_updated", "source": source1.name},
                    {"value": "second_updated", "source": source1.name},
                ],
                param3.name: [{"value": "fourth_updated", "source": source2.name}],
            },
            param2.category.name: {
                param2.name: [{"value": "third_updated", "source": source1.name}],
            },
        },
    )
    assert response.status_code == 404
    dbsession.expire_all()
    assert not info1.is_deleted
    assert not info2.is_deleted
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(param3)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", user_id=1)
def test_param_not_found(dbsession, client, param, source):
    param1 = param()
    param2 = param()
    param3 = Param(
        name=f"test{random_string()}", category_id=param1.category_id, type="all", changeable=True, is_required=True
    )
    dbsession.add(param3)
    source1 = source()
    source2 = source()
    param1.category.update_scope = "test.cat_update.first"
    param2.category.update_scope = "test.cat_update.second"
    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param2.id, owner_id=0)
    dbsession.add_all([info1, info2])
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            f"{param1.category.name}": {
                f"{param1.name}404": [
                    {"value": "first_updated", "source": source1.name},
                    {"value": "second_updated", "source": source1.name},
                ],
                param3.name: [{"value": "fourth_updated", "source": source2.name}],
            },
            param2.category.name: {
                param2.name: [{"value": "third_updated", "source": source1.name}],
            },
        },
    )
    assert response.status_code == 404
    dbsession.expire_all()
    assert not info1.is_deleted
    assert not info2.is_deleted
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(param3)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", user_id=1)
def test_param_and_cat_not_found(dbsession, client, param, source):
    param1 = param()
    param2 = param()
    param3 = Param(
        name=f"test{random_string()}", category_id=param1.category_id, type="all", changeable=True, is_required=True
    )
    dbsession.add(param3)
    source1 = source()
    source2 = source()
    param1.category.update_scope = "test.cat_update.first"
    param2.category.update_scope = "test.cat_update.second"
    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=source2.id, param_id=param2.id, owner_id=0)
    dbsession.add_all([info1, info2])
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            f"{param1.category.name}404": {
                f"{param1.name}404": [
                    {"value": "first_updated", "source": source1.name},
                    {"value": "second_updated", "source": source1.name},
                ],
                param3.name: [{"value": "fourth_updated", "source": source2.name}],
            },
            param2.category.name: {
                param2.name: [{"value": "third_updated", "source": source1.name}],
            },
        },
    )
    assert response.status_code == 404
    dbsession.expire_all()
    assert not info1.is_deleted
    assert not info2.is_deleted
    dbsession.delete(info1)
    dbsession.delete(info2)
    dbsession.delete(param3)
    dbsession.commit()
