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
            "items": [{"category": param.category.name, "param": param.name, "value": "admin_info"}],
        },
    )
    dbsession.expire_all()
    assert response_upd.status_code == 200
    response_get = client.get("/user/0")
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert {"category": param.category.name, "param": param.name, "value": "admin_info"} in list(
        response_get.json()["items"]
    )
    assert {"category": param.category.name, "param": param.name, "value": "user_info"} in list(
        response_get.json()["items"]
    )
    assert len(response_get.json()["items"]) == 2
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
    assert len(response_old.json()["items"]) == 1
    response_upd = client.post(
        f"/user/0",
        json={"source": "admin", "items": [{"category": param.category.name, "param": param.name, "value": None}]},
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert response_get.status_code == 404
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
    assert {"category": param.category.name, "param": param.name, "value": "admin_info"} in list(
        response_old.json()["items"]
    )
    assert len(response_old.json()["items"]) == 1
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "admin",
            "items": [{"category": param.category.name, "param": param.name, "value": "new"}],
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.status_code == 200
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert {"category": param.category.name, "param": param.name, "value": "new"} in list(response_get.json()["items"])
    assert len(response_get.json()["items"]) == 1
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
    assert {"category": param.category.name, "param": param.name, "value": "admin_info"} in list(
        response_old.json()["items"]
    )
    assert len(response_old.json()["items"]) == 1
    response_upd = client.post(
        f"/user/0",
        json={"source": "admin", "items": [{"category": param.category.name, "param": param.name, "value": "new"}]},
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 403
    assert {"category": param.category.name, "param": param.name, "value": "admin_info"} in list(
        response_get.json()["items"]
    )
    assert len(response_get.json()["items"]) == 1
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
    assert {"category": param.category.name, "param": param.name, "value": "admin_info"} in list(
        response_old.json()["items"]
    )
    assert len(response_old.json()["items"]) == 1
    response_upd = client.post(
        f"/user/0",
        json={"source": "admin", "items": [{"category": param.category.name, "param": param.name, "value": "new"}]},
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_get.status_code == 200
    assert response_upd.status_code == 200
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert {"category": param.category.name, "param": param.name, "value": "new"} in list(response_get.json()["items"])
    assert len(response_get.json()["items"]) == 1
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
    assert response_old.status_code == 404
    response_upd = client.post(
        f"/user/0",
        json={"source": "admin", "items": [{"category": param.category.name, "param": param.name, "value": "new"}]},
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_get.status_code == 200
    assert response_upd.status_code == 200
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert {"category": param.category.name, "param": param.name, "value": "new"} in list(response_get.json()["items"])
    assert len(response_get.json()["items"]) == 1
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
        json={"source": "admin", "items": [{"category": param.category.name, "param": param.name, "value": "new"}]},
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_get.status_code == 200
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert response_get.json() == {"items": []}
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
    assert {"category": param.category.name, "param": param.name, "value": "user_info"} in list(
        response_old.json()["items"]
    )
    assert len(response_old.json()["items"]) == 1
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "user",
            "items": [{"category": param.category.name, "param": param.name, "value": "new_user_info"}],
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 200
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert response_get.status_code == 200
    assert {"category": param.category.name, "param": param.name, "value": "new_user_info"} in list(
        response_get.json()["items"]
    )
    assert len(response_get.json()["items"]) == 1
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
    assert {"category": param.category.name, "param": param.name, "value": "user_info"} in list(
        response_old.json()["items"]
    )
    assert len(response_old.json()["items"]) == 1
    response_upd = client.post(
        f"/user/0",
        json={
            "source": "user",
            "items": [{"category": param.category.name, "param": param.name, "value": "new_user_info"}],
        },
    )
    dbsession.expire_all()
    response_get = client.get("/user/0")
    assert response_upd.status_code == 403
    assert response_get.status_code == 200
    assert {"category": param.category.name, "param": param.name, "value": "user_info"} in list(
        response_old.json()["items"]
    )
    assert len(response_old.json()["items"]) == 1
    assert info1.value == "user_info"
    dbsession.delete(info1)
    dbsession.commit()


@pytest.mark.authenticated(user_id=0)
def test_create_new_with_validation(dbsession, client, param, source):
    param = param()
    source = source()
    source.name = "user"
    param.type = "all"
    param.validation = "^validation_[1-3]{3}$"
    dbsession.commit()
    response_upd = client.post(
        f"/user/0",
        json={
            "source": source.name,
            "items": [{"category": param.category.name, "param": param.name, "value": "validation_123"}],
        },
    )
    dbsession.expire_all()
    assert response_upd.status_code == 200
    response_get = client.get("/user/0")
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert {"category": param.category.name, "param": param.name, "value": "validation_123"} in list(
        response_get.json()["items"]
    )
    assert len(response_get.json()["items"]) == 1
    info_new = (
        dbsession.query(Info)
        .filter(Info.param_id == param.id, Info.owner_id == 0, Info.source_id == source.id, Info.is_deleted == False)
        .one()
    )
    dbsession.delete(info_new)
    dbsession.commit()


@pytest.mark.authenticated(user_id=0)
def test_update_with_validation(dbsession, client, param, source):
    param = param()
    source = source()
    source.name = "user"
    param.type = "all"
    param.validation = "^validation_[1-3]{3}$"
    info1 = Info(value="validation_111", source_id=source.id, param_id=param.id, owner_id=0)
    dbsession.add(info1)
    dbsession.commit()
    response_upd = client.post(
        f"/user/0",
        json={
            "source": source.name,
            "items": [{"category": param.category.name, "param": param.name, "value": "validation_222"}],
        },
    )
    dbsession.expire_all()
    assert response_upd.status_code == 200
    response_get = client.get("/user/0")
    assert response_upd.json() == {'status': 'Success', 'message': 'User patch succeeded', 'ru': 'Изменение успешно'}
    assert {"category": param.category.name, "param": param.name, "value": "validation_222"} in list(
        response_get.json()["items"]
    )
    assert len(response_get.json()["items"]) == 1
    info_new = (
        dbsession.query(Info)
        .filter(Info.param_id == param.id, Info.owner_id == 0, Info.source_id == source.id, Info.is_deleted == False)
        .one()
    )
    dbsession.delete(info_new)
    dbsession.commit()


@pytest.mark.authenticated(user_id=0)
def test_create_new_with_failing_validation(dbsession, client, param, source):
    param = param()
    source = source()
    source.name = "user"
    param.type = "all"
    param.validation = "^validation_[1-3]{3}$"
    dbsession.commit()
    response_upd = client.post(
        f"/user/0",
        json={
            "source": source.name,
            "items": [{"category": param.category.name, "param": param.name, "value": "validation_000"}],
        },
    )
    dbsession.expire_all()
    assert response_upd.status_code == 422
    response_get = client.get("/user/0")
    assert response_get.status_code == 404


@pytest.mark.authenticated(user_id=0)
def test_update_with_failing_validation(dbsession, client, param, source):
    param = param()
    source = source()
    source.name = "user"
    param.type = "all"
    param.validation = "^validation_[1-3]{3}$"
    info = Info(value="validation_111", source_id=source.id, param_id=param.id, owner_id=0)
    dbsession.add(info)
    dbsession.commit()
    response_upd = client.post(
        f"/user/0",
        json={
            "source": source.name,
            "items": [{"category": param.category.name, "param": param.name, "value": "validation_000"}],
        },
    )
    dbsession.expire_all()
    assert response_upd.status_code == 422
    response_get = client.get("/user/0")
    assert {"category": param.category.name, "param": param.name, "value": "validation_111"} in list(
        response_get.json()["items"]
    )
    assert len(response_get.json()["items"]) == 1
    dbsession.delete(info)
    dbsession.commit()
