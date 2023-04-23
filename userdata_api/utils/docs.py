import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi_sqlalchemy import db

from userdata_api.utils.user import user_interface


thread_pool = ThreadPoolExecutor()


async def aio_get_openapi(request: Request) -> dict[str, Any]:
    """
    Возвращает текущую версию json'а документации, замена стандартного openapi.json
    :param request: Request  - запрос из FastAPI: https://fastapi.tiangolo.com/advanced/using-request-directly/
    :return: dict[str, Any]
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
