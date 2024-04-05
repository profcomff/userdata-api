from userdata_api.schemas.base import Base


class StatusResponseModel(Base):
    status: str
    message: str
    ru: str
