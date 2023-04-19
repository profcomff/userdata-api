import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from userdata_api.models.db import *
from userdata_api.routes.base import app
from userdata_api.settings import get_settings
from userdata_api.utils.utils import random_string


@pytest.fixture
def _client(auth_mock):
    yield TestClient(app)


@pytest.fixture(scope='session')
def dbsession():
    settings = get_settings()
    engine = create_engine(settings.DB_DSN)
    TestingSessionLocal = sessionmaker(bind=engine)
    yield TestingSessionLocal()


@pytest.fixture
def category(dbsession):
    """
    Вызов создает категорию с двумя рандомными скоупами и возвращщает ее
    """
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
def param(dbsession, category):
    """
    Вызов создает параметр в категории с двумя рандомными скоупами и возвращает его
    """
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
def source(dbsession):
    """
    Вызов создает источник в и возвращает его
    """
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
def info(dbsession, source, param):
    """
    Вызов создает информацмю в с параметром param() и источником source()
    """
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
def category_no_scopes(dbsession):
    """
    Вызов создает категорию без скоупов и возвращает ее
    """
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
def param_no_scopes(dbsession, category_no_scopes):
    """
    Вызов создает параметр в категории без скоупов и возвращает его
    """
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
def info_no_scopes(dbsession, source, param_no_scopes):
    """
    Вызов создает информацию для параметра без скоупов и для источника source() и возвращает ее
    """
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
