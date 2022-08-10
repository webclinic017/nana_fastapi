import sqlalchemy

metadata = sqlalchemy.MetaData()

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("created_order_id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("order_id", sqlalchemy.String, index=True),
    sqlalchemy.Column("status", sqlalchemy.String,),
)


