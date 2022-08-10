from random import randint

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from models.database import database
from models.order import orders
from shemas.shemas_order_cycle import *

router = APIRouter()


@router.post('/lavka/v1/integration-entry/v1/order/submit',
             response_model=OrderResponce,
             responses={400: {'model': OrderValidationError}},
             name='Order Create'
             )
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
    resp = OrderResponce(
        order_id=f"{dat.strftime('%y%m%d')}-{randint(100000, 999999)}"
    )
    query = orders.insert().values(
        order_id=resp.order_id,
        created_order_id=order.created_order_id,
        status='NEW'
    )
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


@router.post('/lavka/v1/integration-entry/v1/order/state',
             response_model=OrdersStateResponse,
             responses={400: {'model': OrderValidationError}, 404: {'model': EmptyResponse}},
             name='Order State'
             )
async def OrderState(order: OrdersStateRequest):
    """
    Find out the status of the order list
    """
    return OrdersStateResponse.get_example()


@router.post('/lavka/v1/integration-entry/v1/order/actions/cancel',
             response_model=EmptyResponse,
             status_code=202,
             responses={400: {'model': EmptyResponse}, 404: {'model': EmptyResponse}},
             name='Order Cancel'
             )
async def OrderState(order: CancelOrderRequest):
    """
    Cancel the order
    """
    return JSONResponse({})


@router.post('/lavka/v1/integration-entry/v1/order/contact/obtain',
             response_model=ContactObtainResponse,
             responses={404: {
                 'model': EmptyResponse, 'name': 'Order not found'}, 409: {'model': EmptyResponse}
             },
             name='Contact Obtain'
             )
async def OrderState(order: ContactObtainRequest):
    """
    Contact Obtain
    """
    return ContactObtainResponse.get_example()


@router.post(
    '/lavka/v1/integration-entry/v1/order/set-payment-status',
    response_model=EmptyResponse,
    responses={404: {'model': EmptyResponse, 'name': 'Order not found'}},
    name='Set Payment Status'
)
async def OrderState(order: SetPaymentStatus):
    """
    Set Payment Status
    """

    return JSONResponse({})
