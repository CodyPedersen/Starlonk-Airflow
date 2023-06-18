"""Basic database/session functionality"""
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Database Setup
HOST = "postgres-db"
DATABASE = "postgres"
PORT = "5432"

USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')

DATABASE_CONNECTION_URI = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'
print(DATABASE_CONNECTION_URI)

# SQL Alchemy
engine = create_engine(DATABASE_CONNECTION_URI) # Create connection to databse
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Individual sessions inherit from me
Base = declarative_base() # Used for models
