import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from models.database import database
from routers import order_cycle, jobs

app = FastAPI(
    title='B2B Api stub',
    description='This stub is designed to test the functionality '
                'of sending messages for integration with yango'
)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({
            "code": "bad_request",
            "message": str(exc.errors()),
            "details": {
                "cart": None,
                "retry_after": 5
            }})
    )

app.include_router(order_cycle.router)
app.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["Jobs"],
)
if __name__ == '__main__':
    uvicorn.run('app:app')
