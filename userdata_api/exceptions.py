class ObjectNotFound(Exception):
    def __init__(self, obj: type, obj_id_or_name: int | str):
        super().__init__(f"Object {obj.__name__} {obj_id_or_name=} not found")


class AlreadyExists(Exception):
    def __init__(self, obj: type, obj_id_or_name: int | str):
        super().__init__(f"Object {obj.__name__} {obj_id_or_name=} already exists")


class Forbidden(Exception):
    def __init__(self, name: str, req_scope: str):
        super().__init__(f"Category {name=}, requires {req_scope=}")
