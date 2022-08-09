import databases
import sqlalchemy
from conf.config import settings
from pydantic import PostgresDsn
from sqlalchemy.orm import sessionmaker
# SQLAlchemy specific code, as with any other app
DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:5432/{settings.DB_NAME}"

SQLALCHEMY_DATABASE_URI = PostgresDsn.build(
    scheme="postgresql",
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    path='/stub',
)
database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

engine = sqlalchemy.create_engine(
    DATABASE_URL
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

