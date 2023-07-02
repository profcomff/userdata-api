from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sqlalchemy import DBSessionMiddleware, db
from starlette.responses import HTMLResponse

from userdata_api import __version__
from userdata_api.schemas.user import user_interface
from userdata_api.settings import get_settings
from userdata_api.utils.docs import aio_get_docs, aio_get_openapi

from .category import category
from .param import param
from .source import source
from .user import user


settings = get_settings()
app = FastAPI(
    title='Сервис пользовательских данных',
    description='Серверная часть сервиса хранения и управления информации о пользователе',
    version=__version__,
    # Отключаем нелокальную документацию
    root_path=settings.ROOT_PATH if __version__ != 'dev' else '/',
    docs_url=None if __version__ != 'dev' else '/docs',
    redoc_url=None,
    openapi_url=None,
)


app.add_middleware(
    DBSessionMiddleware,
    db_url=settings.DB_DSN,
    engine_args={"pool_pre_ping": True, "isolation_level": "AUTOCOMMIT"},
)

if __version__ == 'dev':

    @app.get(app.docs_url, include_in_schema=False)
    async def swagger_ui_html(request: Request) -> HTMLResponse:
        """
        Генериурет страничку сваггера, так как дефолтная отключена

        Работает только в разработческой среде, на проде возвращает 404
        :param request: запрос из fastapi
        :return: Swagger HTML page
        """
        if __version__ != 'dev':
            raise HTTPException(status_code=404)
        return await aio_get_docs(request, openapi_path="/openapi.json")


@app.get("/openapi.json", include_in_schema=False)
async def get_docs(request: Request):
    """
    Фетчит текущую версию документации.
    Обновит при запросе модельки UserGet, UserPost
    """
    app: FastAPI = request.app
    app.openapi_schema = None
    return await aio_get_openapi(request)


@app.on_event("startup")
async def create_models():
    """
    Создает модельки UserGet, UserPost при стартапе приложения
    :return:
    """
    with db():
        await user_interface.refresh(db.session)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(source)
app.include_router(category)
app.include_router(param)
app.include_router(user)
