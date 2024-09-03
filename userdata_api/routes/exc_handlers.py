import starlette
from starlette.responses import JSONResponse

from ..exceptions import AlreadyExists, Forbidden, InvalidRegex, InvalidValidation, ObjectNotFound
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


@app.exception_handler(InvalidValidation)
async def invalid_validation_handler(req: starlette.requests.Request, exc: InvalidValidation):
    return JSONResponse(
        content=StatusResponseModel(status="Invalid validation", message=exc.en, ru=exc.ru).model_dump(),
        status_code=422,
    )


@app.exception_handler(InvalidRegex)
async def invalid_regex_handler(req: starlette.requests.Request, exc: InvalidRegex):
    return JSONResponse(
        content=StatusResponseModel(status="Invalid regex", message=exc.en, ru=exc.ru).model_dump(), status_code=422
    )
