from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi_sqlalchemy import DBSessionMiddleware, db
from pydantic import BaseModel

from userdata_api import __version__
from userdata_api.schemas.user import user_interface
from userdata_api.settings import get_settings

from .category import category
from .info import info
from .param import param
from .source import source
from .user import user


UserModel: BaseModel | None = None

settings = get_settings()
app = FastAPI(
    title='Сервис пользовательских данных',
    description='Серверная часть сервиса хранения и управления информации о пользователе',
    version=__version__,
    # Отключаем нелокальную документацию
    root_path=settings.ROOT_PATH if __version__ != 'dev' else '/',
    docs_url=None if __version__ != 'dev' else '/docs',
    redoc_url=None,
)


app.add_middleware(
    DBSessionMiddleware,
    db_url=settings.DB_DSN,
    engine_args={"pool_pre_ping": True, "isolation_level": "AUTOCOMMIT"},
)


def no_cache_openapi():
    app.openapi_schema = None
    user_interface.refresh(app, db.session)
    app.openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    return app.openapi_schema


app.openapi = no_cache_openapi


@app.on_event("startup")
async def create_models():
    with db():
        user_interface.refresh(app, db.session)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(source)
app.include_router(category)
app.include_router(info)
app.include_router(param)
app.include_router(user)
