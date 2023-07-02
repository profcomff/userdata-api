import pytest

from userdata_api.models.db import *
from userdata_api.utils.utils import random_string


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", "userdata.info.admin", user_id=1)
def test_main_scenario(dbsession, client, param, admin_source):
    param1 = param()
    param2 = param()
    param3 = Param(
        name=f"test{random_string()}", category_id=param1.category_id, type="all", changeable=True, is_required=True
    )
    dbsession.add(param3)
    source1 = admin_source
    param1.category.update_scope = "test.cat_update.first"
    param2.category.update_scope = "test.cat_update.second"
    dbsession.flush()
    info1 = Info(value=f"test{random_string()}", source_id=source1.id, param_id=param1.id, owner_id=0)
    info2_val = f"test{random_string()}"
    info2 = Info(value=info2_val, source_id=source1.id, param_id=param2.id, owner_id=0)

    dbsession.add_all([info1, info2])
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": source1.name,
            param1.category.name: {param1.name: "first_updated", param3.name: "second_updated"},
        },
    )
    assert response.status_code == 200
    dbsession.expire_all()
    assert info1.value == "first_updated"
    assert not info2.is_deleted
    assert info2.value == info2_val
    first: Info = (
        dbsession.query(Info)
        .filter(Info.param_id == param1.id, Info.owner_id == 0, Info.is_deleted == False)
        .one_or_none()
    )
    second: Info = (
        dbsession.query(Info)
        .filter(Info.param_id == param3.id, Info.owner_id == 0, Info.is_deleted == False)
        .one_or_none()
    )
    assert first.value == "first_updated"
    assert second.value == "second_updated"
    response = client.post(f"/user/0", json={"source": source1.name, param2.category.name: {param2.name: None}})
    assert response.status_code == 200
    dbsession.expire_all()
    assert info2.is_deleted
    third = (
        dbsession.query(Info)
        .filter(Info.param_id == param2.id, Info.owner_id == 0, Info.is_deleted == False)
        .one_or_none()
    )
    assert not third
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
        dbsession.query(Info).filter(Info.id == info["id"]).delete()
    for info in second_param:
        dbsession.query(Info).filter(Info.id == info["id"]).delete()
    for info in third_param:
        dbsession.query(Info).filter(Info.id == info["id"]).delete()
    dbsession.commit()
    dbsession.delete(param3)


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", user_id=1)
def test_forbidden_admin(dbsession, client, param, admin_source):
    param1 = param()
    param2 = param()
    param3 = Param(
        name=f"test{random_string()}", category_id=param1.category_id, type="all", changeable=True, is_required=True
    )
    dbsession.add(param3)
    param1.category.update_scope = "test.cat_update.first"
    param2.category.update_scope = "test.cat_update.second"
    info1 = Info(value=f"test{random_string()}", source_id=admin_source.id, param_id=param1.id, owner_id=0)
    info2 = Info(value=f"test{random_string()}", source_id=admin_source.id, param_id=param2.id, owner_id=0)
    dbsession.add_all([info1, info2])
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": admin_source.name,
            f"{param1.category.name}": {param1.name: "first_updated", param3.name: "second_updated"},
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


@pytest.mark.authenticated(user_id=0)
def test_user_update_existing_info(dbsession, client, param, admin_source, source):
    param1 = param()
    user_source = source()
    user_source.name = "user"
    param1.category.update_scope = "test.cat_update.first"
    admin_info = f"test{random_string()}"
    info1 = Info(value=admin_info, source_id=admin_source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "user",
            f"{param1.category.name}": {param1.name: "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 200
    assert not info1.is_deleted
    assert (
        dbsession.query(Info)
        .filter(Info.param_id == param1.id, Info.owner_id == 0, Info.source_id == admin_source.id)
        .one()
        .value
        == admin_info
    )
    new = (
        dbsession.query(Info)
        .join(Source)
        .filter(Info.param_id == param1.id, Info.owner_id == 0, Source.name == "user")
        .one()
    )
    assert new.value == "first_updated"
    dbsession.delete(info1)
    dbsession.delete(new)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", "userdata.info.admin", user_id=1)
def test_category_not_found(dbsession, client, param, admin_source):
    param1 = param()
    param1.category.update_scope = "test.cat_update.first"
    info1 = Info(value=f"test{random_string()}", source_id=admin_source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param1.category.name}404": {param1.name: "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 404
    assert not info1.is_deleted
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", "userdata.info.admin", user_id=1)
def test_param_not_found(dbsession, client, param, admin_source):
    param1 = param()
    param1.category.update_scope = "test.cat_update.first"
    info1 = Info(value=f"test{random_string()}", source_id=admin_source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param1.category.name}": {f"{param1.name}404": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 404
    assert not info1.is_deleted
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "test.cat_update.second", "userdata.info.admin", user_id=1)
def test_param_and_cat_not_found(dbsession, client, param, admin_source):
    param1 = param()
    param1.category.update_scope = "test.cat_update.first"
    info1 = Info(value=f"test{random_string()}", source_id=admin_source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param1.category.name}404": {f"{param1.name}404": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 404
    assert not info1.is_deleted
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", user_id=0)
def test_update_not_changeable(dbsession, client, param, source):
    param1 = param()
    source = source()
    source.name = "user"
    param1.category.update_scope = "test.cat_update.first"
    param1.changeable = False
    info1 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "user",
            f"{param1.category.name}": {f"{param1.name}": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 403
    assert not info1.is_deleted
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", user_id=0)
def test_update_not_changeable_from_admin(dbsession, client, param, admin_source):
    param1 = param()
    param1.category.update_scope = "test.cat_update.first"
    param1.changeable = False
    info1 = Info(value=f"test{random_string()}", source_id=admin_source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param1.category.name}": {f"{param1.name}": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 403
    assert not info1.is_deleted
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated(user_id=0)
def test_param_not_changeable_no_update_scope(dbsession, client, param, source):
    param1 = param()
    source = source()
    source.name = "user"
    param1.category.update_scope = "test.cat_update.first"
    param1.changeable = False
    info1 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "user",
            f"{param1.category.name}": {f"{param1.name}": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 403
    assert not info1.is_deleted
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("userdata.info.update", user_id=0)
def test_param_not_changeable_with_scope(dbsession, client, param, source):
    param1 = param()
    source = source()
    source.name = "user"
    param1.category.update_scope = "test.cat_update.first"
    param1.changeable = False
    info1 = Info(value=f"test{random_string()}", source_id=source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "user",
            f"{param1.category.name}": {f"{param1.name}": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 200
    assert info1.value == "first_updated"
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated(user_id=1)
def test_user_source_requires_information_own(dbsession, client, param, source):
    param1 = param()
    source = source()
    source.name = "user"
    param1.category.update_scope = "test.cat_update.first"
    param1.changeable = False
    info1_value = f"test{random_string()}"
    info1 = Info(value=info1_value, source_id=source.id, param_id=param1.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "user",
            f"{param1.category.name}": {f"{param1.name}": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 403
    assert info1.value == info1_value
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated(user_id=1)
def test_not_available_sources(dbsession, client, param, source):
    param1 = param()
    source = source()
    source.name = "user"
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "not_user",
            f"{param1.category.name}": {f"{param1.name}": "first_updated"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 403


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", user_id=1)
def test_create_new(dbsession, client, param, source, admin_source):
    param = param()
    source = source()
    source.name = "user"
    param.category.update_scope = "test.cat_update.first"
    info1 = Info(value="user_info", source_id=source.id, param_id=param.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": "admin_info"},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 200
    info_new = (
        dbsession.query(Info)
        .filter(
            Info.param_id == param.id, Info.owner_id == 0, Info.source_id == admin_source.id, Info.is_deleted == False
        )
        .one()
    )
    assert not info1.is_deleted
    assert info_new.value == "admin_info"
    dbsession.delete(info_new)
    dbsession.delete(info1)


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", user_id=1)
def test_delete(dbsession, client, param, admin_source):
    param = param()
    info1 = Info(value="admin_info", source_id=admin_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": None},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 200
    assert info1.is_deleted
    dbsession.delete(info1)


@pytest.mark.authenticated("userdata.info.admin", user_id=1)
def test_delete_forbidden_by_category_scope(dbsession, client, param, admin_source):
    param = param()
    info1 = Info(value="admin_info", source_id=admin_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": None},
        },
    )
    dbsession.expire_all()
    assert response.status_code == 403
    assert not info1.is_deleted
    dbsession.delete(info1)
