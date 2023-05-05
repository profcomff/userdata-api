import asyncio
from copy import deepcopy

from pydantic import create_model
from sqlalchemy.orm import Session

from userdata_api.models.db import Category

from .base import Base


class UserInterface:
    """
    Класс, содержащий ссылки на модели для работы с ресурсами польщователей
    и методы для их ообновления при изменении категорий/параметров категорий в БД
    """
    UserGet: type[Base] = create_model("UserGet", __base__=Base)
    UserUpdate: type[Base] = create_model("UserUpdate", __base__=Base)

    @staticmethod
    async def __create_post_model(session: Session) -> type[Base]:
        """
        Создает пайдентик класс по данным из БД
        :param session: Подключение к БД
        :return: пайдентик класс запроса на `POST /user/{id}`
        """
        result = {}
        categories = Category.query(session=session).all()
        info_dict = {"value": (str, ...), "source": (str, ...)}
        info_model: type[Base] = create_model("InfoModelUpdate", **info_dict)
        for category in categories:
            category_dict = {}
            for param in category.params:
                if param.category.name not in result.keys():
                    result[param.category.name] = {}
                category_dict[param.name] = (list[info_model], None)
            _cat = create_model(f"{category.name}__update", __base__=Base, **category_dict)
            result[category.name] = (_cat, None)
        return create_model("UserUpdate", __base__=Base, **result)

    @staticmethod
    async def __create_get_model(session: Session) -> type[Base]:
        """
        Создать модель ответа на `GET /user/{id}`
        :param session: Соеденение с БД
        :return: Пайдентик класс ответа на `GET /user/{id}`
        """
        result = {}
        categories = Category.query(session=session).all()
        for category in categories:
            category_dict = {}
            for param in category.params:
                if param.is_required:
                    category_dict[param.name] = (param.pytype, ...)
                else:
                    category_dict[param.name] = (param.pytype, None)
            model = create_model(f"{category.name}get", __base__=Base, **category_dict)
            result[category.name] = (model, None)
        return create_model("UserGet", __base__=Base, **result)

    @staticmethod
    def __refresh_model(*, origin_model: type[Base], updated_model: type[Base]) -> None:
        """
        Обновляет модель origin_model до состояния updated_model
        :param origin_model: Исходная моделька для обновления
        :param updated_model: Моделька до которой надо ообновить
        :return: None
        """
        fields = updated_model.__fields__
        annotations = updated_model.__annotations__
        origin_model.__fields__ = deepcopy(fields)
        origin_model.__annotations__ = deepcopy(annotations)

    async def _refresh_get_model(self, session: Session) -> None:
        """
        Обновить модель ответа `GET /user/{id}` пользовательских данных
        :param session: Соеденение с БД
        :return: None
        """
        _model: type[Base] = await UserInterface.__create_get_model(session)
        self.__refresh_model(origin_model=self.UserGet, updated_model=_model)

    async def _refresh_update_model(self, session: Session) -> None:
        """
        Обновить модель запроса `POST /user/{id}` пользовательских данных
        :param session: Соеденение с БД
        :return: None
        """
        _model: type[Base] = await UserInterface.__create_post_model(session)
        self.__refresh_model(origin_model=self.UserUpdate, updated_model=_model)

    async def refresh(self, session: Session) -> None:
        """
        Обновляет модель запроса `POST /user/{id}`, модель ответа `GET /user/{id}`
        :param session: Соеденение с БД
        :return: None
        """
        await asyncio.gather(self._refresh_update_model(session), self._refresh_get_model(session))


user_interface = UserInterface()  # Создаем первичные ссылки на пустые объекты, чтобы потом их обновлять
