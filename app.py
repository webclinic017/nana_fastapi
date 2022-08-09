import datetime
import re
from enum import Enum
from random import randint
from typing import List
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, constr
from conf.config import settings
from models.database import database
from models.order import orders

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


class Numeric(str):
    pattern = r'^\d+(\.\d*)?$'

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError(f'str expected, got{type(v)}')
        if not re.match(pattern=cls.pattern, string=v):
            raise ValueError(f'Wrong value {v} for pattern {cls.pattern}')

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

class CartItem(BaseModel):
    id: str
    quantity: Numeric
    full_price: constr(regex=r'^\d+(\.\d*)?$')
    title: Optional[str]
    stack_price: Optional[constr(regex=r'^\d+(\.\d*)?$')]
    stack_full_price: Optional[constr(regex=r'^\d+(\.\d*)?$')]


class Cart(BaseModel):
    items: List[CartItem]
    cart_total_cost: Optional[constr(regex=r'^\d+(\.\d*)?$')]
    cart_total_discount: Optional[constr(regex=r'^\d+(\.\d*)?$')]


class PaymentType(str, Enum):
    cash = 'cash'
    online = 'online'


class Point(BaseModel):
    lat: float
    lon: float

    @validator('lat')
    def lat_min_max(cls, lat):
        if lat > 90 or lat < -90:
            raise ValueError("minimum: -90 or maximum: 90")
        return lat

    @validator('lon')
    def lon_min_max(cls, lon):
        if lon > 180 or lon < -180:
            raise ValueError("minimum: -180 or maximum: 180")
        return lon


class Location(BaseModel):
    position: Point
    place_id: str
    floor: Optional[str]
    flat: Optional[str]
    doorcode: Optional[str]
    doorcode_extra: Optional[str]
    entrance: Optional[str]
    building_name: Optional[str]
    doorbell_name: Optional[str]
    left_at_door: Optional[bool]
    meet_outside: Optional[bool]
    no_door_call: Optional[bool]
    postal_code: Optional[str]
    comment: Optional[str]


class RequestOrder(BaseModel):
    user_id: str
    user_phone: str
    cart: Cart
    payment_type: PaymentType
    location: Location
    created_order_id: Optional[str]
    use_external_delivery: Optional[bool]

class OrderResponce(BaseModel):
    order_id: str
    newbie:  bool = False

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

@app.post('/lavka/v1/integration-entry/v1/order/submit', response_model=OrderResponce)
async def OrderCreate(order: RequestOrder):
    a = settings
    dat = datetime.date.today()
    resp = OrderResponce(order_id=f"{dat.strftime('%y%m%d')}-{randint(100000, 999999)}")
    query = orders.insert().values(order_id=resp.order_id, created_order_id=order.created_order_id, status='NEW')
    last_record_id = await database.execute(query)
    return resp
