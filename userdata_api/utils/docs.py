import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi_sqlalchemy import db

from userdata_api.utils.user_get import user_interface


thread_pool = ThreadPoolExecutor()


async def aio_get_openapi(request: Request) -> dict[str, Any]:
    """
    Возвращает текущую версию json'а документации, замена стандартного openapi.json
    :param request: Request  - запрос из FastAPI: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :return: dict[str, Any]

    Пример:
    ```python
    from fastapi import Request, FastAPI

    app = FastAPI()

    @app.get("/openapi,json")
    async def get_docs(request: Request):
        #do come stuff here
        return await aio_get_openapi(request)
    ```
    """
    app: FastAPI = request.app
    await user_interface.refresh(db.session)
    loop = asyncio.get_event_loop()
    kwargs = dict(
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
    return await loop.run_in_executor(thread_pool, partial(get_openapi, **kwargs))


async def aio_get_docs(request: Request, *, openapi_path: str):
    """
    Генерирует документацию по json'у, лежащему по адресу openapi_path
    :param request: запрос из fastapi
    :param openapi_path: относительный путь до openapi.json
    :return: HTMLResponse - страница Swagger документации

    Приимер:

    ```python
    from fastapi import Request, FastAPI

    app = FastAPI()

    @app.get()
    async def get_docs(request: Request):
        #do come stuff here
        return await aio_get_docs(request)
    ```
    """
    app = request.app
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + openapi_path
    oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if oauth2_redirect_url:
        oauth2_redirect_url = root_path + oauth2_redirect_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=oauth2_redirect_url,
        init_oauth=app.swagger_ui_init_oauth,
        swagger_ui_parameters=app.swagger_ui_parameters,
    )
