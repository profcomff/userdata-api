import random
import string
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pytest_mock import mocker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette import status

from userdata_api.models.db import *
from userdata_api.routes.base import app
from userdata_api.settings import get_settings


@pytest.fixture
def random_string():
    def _random_string():
        return "".join([random.choice(string.ascii_lowercase) for _ in range(12)])

    yield _random_string


@pytest.fixture
def client(mocker):
    user_mock = mocker.patch('auth_lib.fastapi.UnionAuth.__call__')
    user_mock.return_value = {
        "user_id": 0,
        "id": 0,
        "session_scopes": [
            {"id": 0, "name": "userdata.category.create", "comment": ""},
            {"id": 0, "name": "userdata.category.read", "comment": ""},
            {"id": 0, "name": "userdata.category.delete", "comment": ""},
            {"id": 0, "name": "userdata.category.update", "comment": ""},
            {"id": 0, "name": "userdata.param.create", "comment": ""},
            {"id": 0, "name": "userdata.param.read", "comment": ""},
            {"id": 0, "name": "userdata.param.delete", "comment": ""},
            {"id": 0, "name": "userdata.param.update", "comment": ""},
            {"id": 0, "name": "userdata.source.create", "comment": ""},
            {"id": 0, "name": "userdata.source.read", "comment": ""},
            {"id": 0, "name": "userdata.source.delete", "comment": ""},
            {"id": 0, "name": "userdata.source.update", "comment": ""},
            {"id": 0, "name": "userdata.info.read", "comment": ""},
            {"id": 0, "name": "userdata.info.delete", "comment": ""},
            {"id": 0, "name": "userdata.info.update", "comment": ""},
            {"id": 0, "name": "userdata.info.create", "comment": ""},
            {"id": 0, "name": "it.needs.by.test.user.get.first", "comment": ""},
            {"id": 0, "name": "it.needs.by.test.user.get.second", "comment": ""},
            {"id": 0, "name": "it.needs.by.test.user.get.third", "comment": ""},
        ],
        "user_scopes": [
            {"id": 0, "name": "userdata.category.create", "comment": ""},
            {"id": 0, "name": "userdata.category.read", "comment": ""},
            {"id": 0, "name": "userdata.category.delete", "comment": ""},
            {"id": 0, "name": "userdata.category.update", "comment": ""},
            {"id": 0, "name": "userdata.param.create", "comment": ""},
            {"id": 0, "name": "userdata.param.read", "comment": ""},
            {"id": 0, "name": "userdata.param.delete", "comment": ""},
            {"id": 0, "name": "userdata.param.update", "comment": ""},
            {"id": 0, "name": "userdata.source.create", "comment": ""},
            {"id": 0, "name": "userdata.source.read", "comment": ""},
            {"id": 0, "name": "userdata.source.delete", "comment": ""},
            {"id": 0, "name": "userdata.source.update", "comment": ""},
            {"id": 0, "name": "userdata.info.read", "comment": ""},
            {"id": 0, "name": "userdata.info.delete", "comment": ""},
            {"id": 0, "name": "userdata.info.update", "comment": ""},
            {"id": 0, "name": "userdata.info.create", "comment": ""},
        ],
    }
    client = TestClient(app)
    yield client


@pytest.fixture(scope='session')
def dbsession():
    settings = get_settings()
    engine = create_engine(settings.DB_DSN)
    TestingSessionLocal = sessionmaker(bind=engine)
    yield TestingSessionLocal()


@pytest.fixture
def category(dbsession, random_string):
    categories = []
    scopes = []

    def _category():
        nonlocal categories
        nonlocal scopes
        name = f"test{random_string()}"
        __category = Category(name=name)
        dbsession.add(__category)
        dbsession.flush()
        _scope1, _scope2 = Scope(name=f"testscope.{random_string()}", category_id=__category.id), Scope(
            name=f"testscope.{random_string()}", category_id=__category.id
        )
        dbsession.add_all([_scope1, _scope2])
        dbsession.commit()
        categories.append(__category)
        scopes.append(_scope1)
        scopes.append(_scope2)
        return __category

    yield _category
    dbsession.expire_all()
    for row in [category_.scopes for category_ in categories]:
        for _row in row:
            dbsession.delete(_row)
    dbsession.commit()
    for row in categories:
        dbsession.delete(row)
    dbsession.commit()


@pytest.fixture
def param(dbsession, category, random_string):
    params = []

    def _param():
        _category = category()
        nonlocal params
        time_ = f"test{random_string()}"
        __param = Param(name=f"test{time_}", category_id=_category.id, type="last", changeable=True, is_required=True)
        dbsession.add(__param)
        dbsession.commit()
        params.append(__param)
        return __param

    yield _param
    for row in params:
        dbsession.delete(row)
    dbsession.commit()


@pytest.fixture
def source(dbsession, random_string):
    sources = []

    def _source():
        nonlocal sources
        time_ = f"test{random_string()}"
        __source = Source(name=f"test{time_}", trust_level=8)
        dbsession.add(__source)
        dbsession.commit()
        sources.append(__source)
        return __source

    yield _source
    for row in sources:
        dbsession.delete(row)
    dbsession.commit()


@pytest.fixture
def info(dbsession, source, param, random_string):
    infos = []
    _source = source()
    _param = param()

    def _info():
        nonlocal infos
        nonlocal _source
        nonlocal _param
        time_ = f"test{random_string()}"
        __info = Info(value=f"test{time_}", source_id=_source.id, param_id=_param.id, owner_id=0)
        dbsession.add(__info)
        dbsession.commit()
        infos.append(__info)
        return __info

    yield _info
    for row in infos:
        dbsession.delete(row)
    dbsession.commit()


@pytest.fixture
def category_no_scopes(dbsession, random_string):
    categories = []

    def _category_no_scopes():
        nonlocal categories
        name = f"test{random_string()}"
        __category = Category(name=name)
        dbsession.add(__category)
        dbsession.commit()
        categories.append(__category)
        return __category

    yield _category_no_scopes
    dbsession.expire_all()
    for row in categories:
        dbsession.delete(row)
    dbsession.commit()


@pytest.fixture
def param_no_scopes(dbsession, category_no_scopes, random_string):
    params = []
    _category = category_no_scopes()

    def _param_no_scopes():
        nonlocal _category
        nonlocal params
        time_ = f"test{random_string()}"
        __param = Param(name=f"test{time_}", category_id=_category.id, type="last", changeable=True, is_required=True)
        dbsession.add(__param)
        dbsession.commit()
        params.append(__param)
        return __param

    yield _param_no_scopes
    for row in params:
        dbsession.delete(row)
    dbsession.commit()


@pytest.fixture
def info_no_scopes(dbsession, source, param_no_scopes, random_string):
    infos = []

    def _info_no_scopes():
        nonlocal infos
        _source = source()
        _param = param_no_scopes()
        time_ = f"test{random_string()}"
        __info = Info(value=f"test{time_}", source_id=_source.id, param_id=_param.id, owner_id=0)
        dbsession.add(__info)
        dbsession.commit()
        infos.append(__info)
        return __info

    yield _info_no_scopes
    for row in infos:
        dbsession.delete(row)
    dbsession.commit()
