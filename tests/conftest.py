import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from userdata_api.models.db import *
from userdata_api.routes.base import app
from userdata_api.settings import get_settings
from userdata_api.utils.utils import random_string


@pytest.fixture
def client(auth_mock):
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
    Вызов фабрики создает категорию с двумя рандомными скоупами и возвращщает ее
    ```
    def test(category):
        category1 = category()
        category2 = category()
    ```
    """
    categories = []

    def _category():
        nonlocal categories
        name = f"test{random_string()}"
        __category = Category(
            name=name, read_scope=f"testscope.{random_string()}", update_scope=f"testscope.{random_string()}"
        )
        dbsession.add(__category)
        dbsession.commit()
        categories.append(__category)
        return __category

    yield _category
    dbsession.expire_all()
    dbsession.commit()
    for row in categories:
        dbsession.delete(row)
    dbsession.commit()


@pytest.fixture
def param(dbsession, category):
    """
    ```
    Вызов фабрики создает параметр в категории с двумя рандомными скоупами и возвращает его
    В рамках одного теста параметры создаются в разных категориях - для каждого параметра своя категория
    def test(param):
        param1 = param()
        param2 = param()
    ```
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
    Вызов фабрики создает источник в и возвращает его
    ```
    def test(source):
        source1 = source()
        source2 = source()
    ```
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
def category_no_scopes(dbsession):
    """
    Вызов фабрики создает категорию без скоупов и возвращает ее
    ```
    def test(category_no_scopes):
        category_no_scopes1 = category_no_scopes()
        category_no_scopes2 = category_no_scopes()
    ```
    """
    categories = []

    def _category_no_scopes():
        nonlocal categories
        name = f"test{random_string()}"
        __category = Category(name=name, read_scope=None, update_scope=None)
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
    Вызов фабрики создает параметр в категории без скоупов и возвращает его

    Все созданные параметры в рамках одного теста принадлежат одной категории
    ```
    def test(param_no_scopes):
        param_no_scopes1 = param_no_scopes()
        param_no_scopes2 = param_no_scopes()
    ```
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
    Вызов фабрики создает информацию для параметра без скоупов и для источника source() и возвращает ее

    Все сущности info принадлежат разным параметрам, которые принадлежат одной категории.

    Источники для всех сущностей разные.
    ```
    def test(info_no_scopes):
        info_no_scopes1 = info_no_scopes()
        info_no_scopes2 = info_no_scopes()
    ```
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
