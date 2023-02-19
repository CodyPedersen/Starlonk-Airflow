from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os


# Database Setup
host = "postgres-db"
database = "postgres"
port = "5432"

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')


DATABASE_CONNECTION_URI = f'postgresql://{user}:{password}@{host}:{port}/{database}'
print(DATABASE_CONNECTION_URI)

# SQL Alchemy
engine = create_engine(DATABASE_CONNECTION_URI) # Create connection to databse
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Individual sessions inherit from me
Base = declarative_base() # Used for models
