import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
load_dotenv()

DB_CONNECTION_STR = os.getenv("DB_CONNECTION_STR")
if DB_CONNECTION_STR is None:
    raise ValueError("DB_CONNECTION_STR not found in environment variables")
engine = create_engine(DB_CONNECTION_STR)