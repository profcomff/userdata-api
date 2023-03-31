class ObjectNotFound(Exception):
    def __init__(self, obj: type, obj_id_or_name: int | str):
        super().__init__(f"Object {obj.__name__} {obj_id_or_name=} not found")