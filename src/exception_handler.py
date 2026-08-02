from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi import status

# TODO: Update the response accordingly

def register_exception_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        try:
            errors = [
                {
                    "field": ".".join(str(loc) for loc in error['loc']),
                    "message": error['msg'],
                    "type": error['type']
                } for error in exc.errors()
            ]
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "success": False,
                    "error": errors,
                    "message": "Validation failed for one or more fields"
                }
            )
        except HTTPException:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Unexpected error")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        try:
            sanitized_detail = jsonable_encoder(exc.detail)
            return JSONResponse(status_code=exc.status_code, content=sanitized_detail)
        except Exception:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Unexpected error")
