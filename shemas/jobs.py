from pydantic import BaseModel


class ProductSync(BaseModel):
    token: str


class Product(BaseModel):
    product_id: str
    external_id: str
