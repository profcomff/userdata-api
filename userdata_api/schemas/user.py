from copy import deepcopy
from functools import wraps
from typing import Awaitable, Callable, ParamSpec, TypeVar

from fastapi import FastAPI, Request
from fastapi_sqlalchemy import db
from pydantic import create_model
from sqlalchemy.orm import Session

from userdata_api.models.db import Category

from .base import Base


class UserInterface:
    User: type[Base] = create_model("User", __base__=Base)

    @staticmethod
    async def __create_model(session: Session) -> type[Base]:
        result = {}
        categories = Category.query(session=session).all()
        for category in categories:
            category_dict = {}
            for param in category.params:
                if param.is_required:
                    category_dict[param.name] = (param.pytype, ...)
                else:
                    category_dict[param.name] = (param.pytype, None)
            model = create_model(category.name, __base__=Base, **category_dict)
            result[category.name] = (model, None)
        return create_model("User", __base__=Base, **result)

    async def refresh(self, session: Session):
        _model: type[Base] = await UserInterface.__create_model(session)
        fields = _model.__fields__
        annotations = _model.__annotations__
        self.User.__fields__ = deepcopy(fields)
        self.User.__annotations__ = deepcopy(annotations)
        del fields, annotations, _model


user_interface = UserInterface()


T = TypeVar("T")
P = ParamSpec("P")


def refreshing(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """
    Декоратор для обертки функций обновляющих модель ответа `GET /user/{user_id}`
    Первым аргументом ручки должен быть request.
    """

    @wraps(fn)
    async def decorated(request: Request, *args: P.args, **kwargs: P.kwargs) -> T:
        app: FastAPI = request.app
        _res = await fn(request, *args, **kwargs)
        await user_interface.refresh(db.session)
        app.openapi_schema = None
        return _res

    return decorated
