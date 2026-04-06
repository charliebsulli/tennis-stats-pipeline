import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

engine = create_engine(os.getenv("DB_CONNECTION_STR"))


def get_conn():
    with engine.connect() as conn:
        yield conn
