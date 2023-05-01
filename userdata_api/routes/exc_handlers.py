import starlette
from starlette.responses import JSONResponse

from ..exceptions import Forbidden, ObjectNotFound
from ..schemas.response_model import ResponseModel
from .base import app


@app.exception_handler(ObjectNotFound)
async def not_found_handler(req: starlette.requests.Request, exc: ObjectNotFound):
    return JSONResponse(content=ResponseModel(status="Error", message=f"{exc}").dict(), status_code=404)


@app.exception_handler(Forbidden)
async def not_found_handler(req: starlette.requests.Request, exc: Forbidden):
    return JSONResponse(content=ResponseModel(status="Forbidden", message=f"{exc}").dict(), status_code=403)
