class UserDataApiError(Exception):
    def __init__(self, error_en: str, error_ru: str) -> None:
        self.en = error_en
        self.ru = error_ru
        super().__init__(error_en)


class ObjectNotFound(UserDataApiError):
    def __init__(self, obj: type, obj_id_or_name: int | str):
        super().__init__(
            f"Object {obj.__name__} {obj_id_or_name=} not found",
            f"Объект {obj.__name__} с идиентификатором {obj_id_or_name=} не найден",
        )


class AlreadyExists(UserDataApiError):
    def __init__(self, obj: type, obj_id_or_name: int | str):
        super().__init__(
            f"Object {obj.__name__} {obj_id_or_name=} already exists",
            f"Объект {obj.__name__} с идиентификатором {obj_id_or_name=} уже существует",
        )


class Forbidden(UserDataApiError):
    pass
