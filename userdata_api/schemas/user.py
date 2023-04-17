from copy import deepcopy
from typing import ParamSpec, TypeVar

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
