from userdata_api.schemas.base import Base


class ResponseModel(Base):
    status: str
    message: str