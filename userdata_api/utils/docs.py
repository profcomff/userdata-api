import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi


thread_pool = ThreadPoolExecutor()


async def aio_get_openapi(request: Request):
    app = request.app
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
