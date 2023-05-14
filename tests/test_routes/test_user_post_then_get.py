import pytest

from userdata_api.models.db import Info


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", "test.cat_read.first", user_id=1)
def test_create_new(dbsession, client, param, source, admin_source):
    param = param()
    source = source()
    source.name = "user"
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    param.type = "all"
    info1 = Info(value="user_info", source_id=source.id, param_id=param.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    client.get("/user/0")
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": "admin_info"},
        },
    )
    dbsession.expire_all()
    assert response_upd.status_code == 200
    response_get = client.get("/user/0")
    assert response_get.json() == response_upd.json()
    assert response_get.json()[param.category.name]
    assert "admin_info" in response_get.json()[param.category.name][param.name]
    assert "user_info" in response_get.json()[param.category.name][param.name]
    assert len(response_get.json()[param.category.name][param.name]) == 2
    info_new = (
        dbsession.query(Info)
        .filter(
            Info.param_id == param.id, Info.owner_id == 0, Info.source_id == admin_source.id, Info.is_deleted == False
        )
        .one()
    )
    dbsession.delete(info_new)
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", "test.cat_read.first", user_id=1)
def test_delete(dbsession, client, param, admin_source):
    param = param()
    param.type = "all"
    info1 = Info(value="admin_info", source_id=admin_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.add(info1)
    dbsession.commit()
    response_old = client.get("/user/0")
    assert response_old.json()[param.category.name][param.name] == ["admin_info"]
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": None},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.json() == response_upd.json()
    assert response_get.json() == {}
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", "test.cat_read.first", user_id=1)
def test_update(dbsession, client, param, admin_source):
    param = param()
    param.type = "all"
    info1 = Info(value="admin_info", source_id=admin_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.add(info1)
    dbsession.commit()
    response_old = client.get("/user/0")
    assert response_old.json()[param.category.name][param.name] == ["admin_info"]
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": "new"},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.json() == response_upd.json()
    assert response_get.json()[param.category.name][param.name] == ["new"]
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", "test.cat_read.first", user_id=1)
def test_update_not_changeable(dbsession, client, param, admin_source):
    param = param()
    param.type = "all"
    param.changeable = False
    info1 = Info(value="admin_info", source_id=admin_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.add(info1)
    dbsession.commit()
    response_old = client.get("/user/0")
    assert response_old.json()[param.category.name][param.name] == ["admin_info"]
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": "new"},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 403
    assert response_get.json()[param.category.name][param.name] == ["admin_info"]
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated(
    "test.cat_update.first", "userdata.info.admin", "test.cat_read.first", "userdata.info.update", user_id=1
)
def test_update_not_changeable_with_scopes(dbsession, client, param, admin_source):
    param = param()
    param.type = "all"
    param.changeable = False
    info1 = Info(value="admin_info", source_id=admin_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.add(info1)
    dbsession.commit()
    response_old = client.get("/user/0")
    assert response_old.json()[param.category.name][param.name] == ["admin_info"]
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": "new"},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.json() == response_upd.json()
    assert response_get.json()[param.category.name][param.name] == ["new"]
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", "test.cat_read.first", user_id=1)
def test_create_new_no_category(dbsession, client, param, admin_source):
    param = param()
    param.type = "all"
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.commit()
    response_old = client.get("/user/0")
    assert response_old.json() == {}
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": "new"},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.json() == response_upd.json()
    assert response_get.json()[param.category.name][param.name] == ["new"]
    info_new = (
        dbsession.query(Info)
        .filter(
            Info.param_id == param.id, Info.owner_id == 0, Info.source_id == admin_source.id, Info.is_deleted == False
        )
        .one()
    )
    dbsession.delete(info_new)
    dbsession.commit()


@pytest.mark.authenticated("test.cat_update.first", "userdata.info.admin", user_id=1)
def test_update_no_read_scope(dbsession, client, param, admin_source):
    param = param()
    param.type = "all"
    info1 = Info(value="admin_info", source_id=admin_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.add(info1)
    dbsession.commit()
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            f"{param.category.name}": {f"{param.name}": "new"},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.json() == response_upd.json()
    assert response_get.json() == {}
    assert info1.value == "new"
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated(user_id=0)
def test_update_from_user_source(dbsession, client, param, source):
    param = param()
    param.type = "all"
    _source = source()
    _source.name = "user"
    info1 = Info(value="user_info", source_id=_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.add(info1)
    dbsession.commit()
    response_old = client.get("/user/0")
    assert response_old.json()[param.category.name][param.name] == ["user_info"]
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "user",
            f"{param.category.name}": {f"{param.name}": "new_user_info"},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.json() == response_upd.json()
    assert response_get.json()[param.category.name][param.name] == ["new_user_info"]
    assert info1.value == "new_user_info"
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated(user_id=0)
def test_update_from_user_source_not_changeable(dbsession, client, param, source):
    param = param()
    param.type = "all"
    param.changeable = False
    _source = source()
    _source.name = "user"
    info1 = Info(value="user_info", source_id=_source.id, param_id=param.id, owner_id=0)
    param.category.update_scope = "test.cat_update.first"
    param.category.read_scope = "test.cat_read.first"
    dbsession.add(info1)
    dbsession.commit()
    response_old = client.get("/user/0")
    assert response_old.json()[param.category.name][param.name] == ["user_info"]
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "user",
            f"{param.category.name}": {f"{param.name}": "new_user_info"},
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 403
    assert response_get.json() != response_upd.json()
    assert response_get.json()[param.category.name][param.name] == ["user_info"]
    assert info1.value == "user_info"
    dbsession.delete(info1)
    dbsession.commit()
