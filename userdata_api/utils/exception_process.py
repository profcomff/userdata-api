from userdata_api.exceptions import Forbidden, ObjectNotFound
from userdata_api.models.db import Category


def __get_process_exception(category: Category, category_name: str, scope_names: list[str]) -> Exception:
    """
    Возвращает исключение, если категория не была найдена или право на ее изменение отсутствет в правах сессии
    :param category: Категория, может быть None
    :param category_name: Имя запрашиваемой категории
    :param scope_names: Список имен скоупов сессии
    :return: Исключение, вызванное в результате проверки

    Пример:

    ```
    from fastapi import Depends, FastAPI

    app = FastAPI()

    @app.get("/{id}")
    async def example(id: int, user = Depends(UnionAuth(scopes=[]))):
        category = db.session.query(Category).get(id)
        exc = __get_process_exception(category, [scope["name"] for scope in user["session_scopes"]])
        if exc:
            raise exc
        #do some stuff here
        return category
    ```
    """
    _exc = None
    if not category:
        _exc = ObjectNotFound(Category, category_name)
    elif category.update_scope not in scope_names:
        _exc = Forbidden(category.name, category.update_scope)
    return _exc
