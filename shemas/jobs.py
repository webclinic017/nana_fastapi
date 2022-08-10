from pydantic import BaseModel


class Product(BaseModel):
    product_id: str
    external_id: str
