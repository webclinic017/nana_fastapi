import sqlalchemy

metadata = sqlalchemy.MetaData()

products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("product_id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("external_id", sqlalchemy.String, index=True),
)


