import starlette
from starlette.responses import JSONResponse

from ..exceptions import AlreadyExists, Forbidden, ObjectNotFound
from ..schemas.response_model import StatusResponseModel
from .base import app


@app.exception_handler(ObjectNotFound)
async def not_found_handler(req: starlette.requests.Request, exc: ObjectNotFound):
    return JSONResponse(
        content=StatusResponseModel(status="Error", message=exc.en, ru=exc.ru).model_dump(), status_code=404
    )


@app.exception_handler(Forbidden)
async def forbidden_handler(req: starlette.requests.Request, exc: Forbidden):
    return JSONResponse(
        content=StatusResponseModel(status="Forbidden", message=exc.en, ru=exc.ru).model_dump(), status_code=403
    )


@app.exception_handler(AlreadyExists)
async def already_exists_handler(req: starlette.requests.Request, exc: AlreadyExists):
    return JSONResponse(
        content=StatusResponseModel(status="Already exists", message=exc.en, ru=exc.ru).model_dump(), status_code=409
    )
