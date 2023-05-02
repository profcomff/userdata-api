from userdata_api.exceptions import Forbidden, ObjectNotFound
from userdata_api.models.db import Category


def __get_process_exception(category: Category, category_name: str, scope_names: list[str]) -> Exception:
    _exc = None
    if not category:
        _exc = ObjectNotFound(Category, category_name)
    elif category.update_scope not in scope_names:
        _exc = Forbidden(category.name, category.update_scope)
    return _exc
