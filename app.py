import datetime
import re, json
from enum import Enum
from random import randint
from typing import List
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, constr, Field, conint
from conf.config import settings
from models.database import database
import uvicorn
from models.order import orders
from asyncpg.exceptions import UniqueViolationError

app = FastAPI(title='B2B Api stub', description='This stub is designed to test the functionality of sending messages for integration with yango')

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
    """
    An item inside a cart
    """
    id: str = Field(description='Partner item id')
    quantity: Numeric = Field(description='Item quantity', title='Basically Decimal <4>')
    full_price: Numeric = Field(description='Basic price of an item', title='Basically Decimal <4>')
    title: Optional[str] = Field(description='Item title')
    stack_price: Optional[Numeric] = Field(description='Resulting price of a full stack', title='Basically Decimal <4>')
    stack_full_price: Optional[Numeric] = Field(description='Basic price of a full stack', title='Basically Decimal <4>')

    class Config:
        title = 'Cart item'

class Cart(BaseModel):
    items: List[CartItem] = Field(description='Items in a cart')
    cart_total_cost: Optional[Numeric] = Field(description='Total cost', title='Basically Decimal <4>')
    cart_total_discount: Optional[Numeric] = Field(description='Total discount', title='Basically Decimal <4>')


class PaymentType(str, Enum):
    cash = 'cash'
    online = 'online'


class Point(BaseModel):
    lat: float = Field(description='Latitude')
    lon: float = Field(description='Latitude')

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
    position: Point = Field(description='Сoordinates of the point')
    place_id: str = Field(description='URI')
    floor: Optional[str] = Field(description='Floor number')
    flat: Optional[str] = Field(description='Flat number')
    doorcode: Optional[str] = Field(description='Basic intercom code')
    doorcode_extra: Optional[str] = Field(description='Additional info for intercom')
    entrance: Optional[str] = Field(description='Entrance')
    building_name: Optional[str] = Field(description='Name of an apartment complex')
    doorbell_name: Optional[str] = Field(description='Who do you call in intercom')
    left_at_door: Optional[bool] = Field(description='Leave order at door')
    meet_outside: Optional[bool] = Field(description='Courier will be met outside')
    no_door_call: Optional[bool] = Field(description='Do not use intercom (call by phone instead)')
    postal_code: Optional[str] = Field(description='For certain countries postal code is very important')
    comment: Optional[str] = Field(description='Address comment')


class RequestOrder(BaseModel):
    user_id: str = Field(description='Id of a user who placed an order')
    user_phone: str = Field(description='User phone numbe')
    cart: Cart = Field(description='The shopping cart associated with an order')
    payment_type: PaymentType = Field(description='Payment related to an order')
    location: Location = Field(description='Location and delivery details')
    created_order_id: Optional[str] = Field(description='Order id as already created by client system')
    use_external_delivery: Optional[bool] = Field(description='Do not use our delivery, only build order')

class OrderResponce(BaseModel):
    order_id: str = Field(description='Yango order id')
    newbie:  bool = False

class OrderValidationErrorDetails(BaseModel):
    cart: None
    retry_after: int

class OrderValidationError(BaseModel):
    code: str
    message:  str
    details: OrderValidationErrorDetails

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

@app.post('/lavka/v1/integration-entry/v1/order/submit', response_model=OrderResponce, responses={400: {'model': OrderValidationError}}, name='Order Create')
async def OrderCreate(order: RequestOrder):
    """
    Creating an order in the yango infrastructure
    Need to pass the main parameters,
    - the client,
    - location,
    - information about the cart,
    - and other parameters
    """
    dat = datetime.date.today()
    resp = OrderResponce(order_id=f"{dat.strftime('%y%m%d')}-{randint(100000, 999999)}")

    query = orders.insert().values(order_id=resp.order_id, created_order_id=order.created_order_id, status='NEW')
    try:
        await database.execute(query)
    except UniqueViolationError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({
                "code": "grocery_order_id_exists",
                "message": str(exc),
                "details": {
                    "cart": None,
                    "retry_after": 5
                }})
        )
    return resp

class DeliveryType(str, Enum):
    courier = 'courier'
    pickup = 'pickup'
    rover = 'rover'

class OrderStatus(str, Enum):
    created = 'created'
    assembling = 'assembling'
    assembled = 'assembled'
    performer_found = 'performer_found'
    delivering = 'delivering'
    delivery_arrived = 'delivery_arrived'
    closed = 'closed'

class OrderResolution(str, Enum):
    succeeded = 'succeeded'
    canceled = 'canceled'
    failed = 'failed'

class OrdersStateRequest(BaseModel):
    user_id: Optional[str]
    known_orders: List[str]

class OrderActionType(str, Enum):
    cancel = 'cancel'
    call_courier = 'call_courier'
    rover_open_hatch = 'rover_open_hatch'


class OrderAction(BaseModel):
    type: OrderActionType

class CargoDispatchInfo(BaseModel):
    dispatch_in_batch: Optional[bool]
    batch_order_num: Optional[int]

class StateCourierInfo(BaseModel):
    name: Optional[str]
    transport_type: Optional[str]
    position: Optional[Point]
    cargo_dispatch_info: Optional[CargoDispatchInfo]
    car_number: Optional[str]
    driver_id: Optional[str]

class OrderInfo(BaseModel):
    id: str
    short_order_id: str
    delivery_type: DeliveryType
    address: str
    status: OrderStatus
    delivery_eta_min: conint(gt=0)
    resolution: OrderResolution
    actions: List[OrderAction]
    courier_info: StateCourierInfo
    address: Location
    depot_location: Point
    promise_max: datetime.datetime

    @staticmethod
    def get_example():
        return OrderInfo(**{
            'id': '3422b448-2460-4fd2-9183-8000de6f8343',
            'short_order_id': '2000-3213-23',
            'delivery_type': 'courier',
            'address': {
                'position': {'lat': 20, 'lon': 20},
                'place_id': '2018391'
            },
            'status': 'created',
            'delivery_eta_min': 20,
            'resolution': 'succeeded',

            'actions': [{'type': 'call_courier'}],
            'courier_info': {
                'position': {'lat': 20, 'lon': 20},
                'cart_id': {
                    'items': [
                        {
                            'id': 'PID10268711',
                            'quantity': '4',
                            'full_price': '5.23'
                        },
                        {
                            'id': 'PID10279131',
                            'quantity': '1',
                            'full_price': '2.15'
                        }
                    ]
                }
            },
            'depot_location': {
                'lat': 20,
                'lon': 20
            },
            'promise_max': '2022-08-10T16:22:18'
        })

class OrdersStateResponse(BaseModel):
    grocery_orders: List[OrderInfo]

    @staticmethod
    def get_example():
        return OrdersStateResponse(grocery_orders=[OrderInfo.get_example()])

class EmptyResponse(BaseModel):
    pass

@app.post('/lavka/v1/integration-entry/v1/order/state', response_model=OrdersStateResponse, responses={400: {'model': OrderValidationError}, 404: {'model': EmptyResponse}}, name='Order State')
async def OrderState(order: OrdersStateRequest):
    """
    Find out the status of the order list
    """
    return OrdersStateResponse.get_example()

class CancelOrderReason(BaseModel):
    type: Optional[constr(max_length=128)]


class CancelOrderType(str, Enum):
    logical = 'logical'
    user = 'user'


class CancelOrderRequest(BaseModel):
    order_id: str = Field(description='Partner order id')
    reason: Optional[CancelOrderReason]
    cancel_type: Optional[CancelOrderType]

    @staticmethod
    def get_example():
        return CancelOrderRequest(order_id='3422b448-2460-4fd2-9183-8000de6f8343')


@app.post('/lavka/v1/integration-entry/v1/order/actions/cancel', response_model=EmptyResponse, status_code=202, responses={400: {'model': EmptyResponse}, 404: {'model': EmptyResponse}}, name='Order Cancel')
async def OrderState(order: CancelOrderRequest):
    """
    Cancel the order
    """

    return JSONResponse({})


class ContactObtainRequest(BaseModel):
    order_id: str

class ContactObtainResponse(BaseModel):
    phone: str
    ext: str

    @staticmethod
    def get_example():
        return ContactObtainResponse(phone='+966582904515', ext='231')

@app.post('/lavka/v1/integration-entry/v1/order/contact/obtain', response_model=ContactObtainResponse, responses={404: {'model': EmptyResponse, 'name': 'Order not found'}, 409: {'model': EmptyResponse}}, name='Contact Obtain')
async def OrderState(order: ContactObtainRequest):
    """
    Contact Obtain
    """

    return ContactObtainResponse.get_example()

class payment_status(str, Enum):
    success = 'success'
    fail = 'fail'

class SetPaymentStatus(BaseModel):
    order_id: str
    payment_status: Optional[payment_status]
    payment_type: Optional[PaymentType] = Field(description='Payment related to an order')

@app.post('/lavka/v1/integration-entry/v1/order/set-payment-status', response_model=EmptyResponse, responses={404: {'model': EmptyResponse, 'name': 'Order not found'}}, name='Set Payment Status')
async def OrderState(order: SetPaymentStatus):
    """
    Set Payment Status
    """

    return JSONResponse({})


if __name__ == '__main__':
    uvicorn.run('app:app')


