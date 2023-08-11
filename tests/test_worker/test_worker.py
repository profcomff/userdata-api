import pytest
import sqlalchemy.exc
from event_schema.auth import UserLogin

from userdata_api.models.db import Category, Info, Param, Source
from userdata_api.utils.utils import random_string
from worker.backends.mock import ConsumerMock


@pytest.fixture()
def category(dbsession):
    name = f"test{random_string()}"
    dbsession.add(
        _cat := Category(
            name=name, read_scope=f"testscope.{random_string()}", update_scope=f"testscope.{random_string()}"
        )
    )
    dbsession.commit()
    yield _cat
    dbsession.delete(_cat)
    dbsession.commit()


@pytest.fixture()
def param(dbsession, category):
    time_ = f"test{random_string()}"
    dbsession.add(
        _par := Param(name=f"test{time_}", category_id=category.id, type="last", changeable=True, is_required=True)
    )
    dbsession.commit()
    yield _par
    dbsession.delete(_par)
    dbsession.commit()


@pytest.fixture()
def source(dbsession):
    time_ = f"test{random_string()}"
    __source = Source(name=f"test{time_}", trust_level=8)
    dbsession.add(__source)
    dbsession.commit()
    yield __source
    dbsession.delete(__source)
    dbsession.commit()


@pytest.fixture()
def info(param, source, dbsession):
    time_ = f"test{random_string()}"
    __info = Info(value=f"test{time_}", source_id=source.id, param_id=param.id, owner_id=1)
    dbsession.add(__info)
    dbsession.commit()
    yield __info
    try:
        dbsession.delete(__info)
        dbsession.commit()
    except sqlalchemy.exc.Any:
        pass


@pytest.fixture()
def consumer():
    yield (cons := ConsumerMock())
    cons.close()


def test_create(consumer, param, source, dbsession):
    with pytest.raises(sqlalchemy.exc.NoResultFound):
        dbsession.query(Info).filter(Info.param_id == param.id, Info.source_id == source.id, Info.value == "test").one()
    consumer._patch_user_info(
        UserLogin.model_validate(
            {"items": [{"category": param.category.name, "param": param.name, "value": "test"}], "source": source.name}
        ),
        1,
    )
    info = (
        dbsession.query(Info).filter(Info.param_id == param.id, Info.source_id == source.id, Info.value == "test").one()
    )
    assert info
    dbsession.delete(info)
    dbsession.commit()


def test_update(info, dbsession, consumer):
    assert info.value != "updated"
    consumer._patch_user_info(
        UserLogin.model_validate(
            {
                "items": [{"category": info.category.name, "param": info.param.name, "value": "updated"}],
                "source": info.source.name,
            }
        ),
        1,
    )

    dbsession.expire(info)
    assert info.value == "updated"


def test_delete(info, dbsession, consumer):
    assert info.is_deleted is False
    consumer._patch_user_info(
        UserLogin.model_validate(
            {
                "items": [{"category": info.category.name, "param": info.param.name, "value": None}],
                "source": info.source.name,
            }
        ),
        1,
    )

    dbsession.expire(info)
    assert info.is_deleted is True
