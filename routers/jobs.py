import aiohttp
from fastapi import BackgroundTasks, APIRouter, Request
from fastapi.exceptions import RequestValidationError
from asyncpg.exceptions import UniqueViolationError
from models.database import database
from functools import wraps
from conf.config import settings
from models.product import products
from shemas.jobs import Product
from typing import List

router = APIRouter()


async def sync_product_from_wms():
    body = {
        "cursor": '1',
        "locale": "saudi_arabica"
    }
    async with aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {settings.wms_token}'}) as session:
        while body.get('cursor'):
            async with session.post(
                    f'{settings.wms_url}/api/external/products/v1/products',
                    json=body,
                    verify_ssl=False) as resp:
                resp = await resp.json()
            for product in resp.get('products'):
                query = products.insert().values(
                    product_id=product['product_id'],
                    external_id=product['external_id']
                )
                try:
                    await database.execute(query)
                    print(f"Created product: {product['external_id']}")
                except UniqueViolationError:
                    print(f"Updated product: {product['external_id']}")
                    continue
            body['cursor'] = resp.get('cursor', None)


def token_required(func):
    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        token = request.headers.get('authorization')
        if token:
            if not settings.wms_token in token.split():
                raise RequestValidationError(f'Wrong token {token}')
        # my_header will be now available in decorator
        return await func(*args, request, **kwargs)
    return wrapper


@router.post("/sync-products", name='Sync WMS Products')
@token_required
async def sync_products(request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_product_from_wms)
    return {"message": "Notification sent in the background"}


@router.get("/get-products", name='Get all products', response_model=List[Product])
@token_required
async def get_products(request: Request):
    query = products.select()
    data = await database.fetch_all(query)
    return data
