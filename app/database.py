#!/usr/bin/env python3
"""
This module handles the database connection and session management for the
application. It includes functions for creating the database and tables,
as well as providing a session generator for database operations.
"""
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import getenv
from .models import Base

load_dotenv()


# Environment variables for MySQL configuration
CG_MYSQL_USER = getenv('CG_MYSQL_USER')
CG_MYSQL_PWD = getenv('CG_MYSQL_PWD')
CG_MYSQL_HOST = getenv('CG_MYSQL_HOST')
CG_MYSQL_DB = getenv('CG_MYSQL_DB')
CG_ENV = getenv('CG_ENV')

# MySQL connection string
MYSQL_ENDPOINT = 'mysql+mysqldb://{}:{}@{}/{}'.format(
    CG_MYSQL_USER,
    CG_MYSQL_PWD,
    CG_MYSQL_HOST,
    CG_MYSQL_DB
)
# print(MYSQL_ENDPOINT)

# SQLite engine for local testing
engine = create_engine(MYSQL_ENDPOINT)

# Session factory for database operations
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    """
    Provides a database session for dependency injection in FastAPI routes.

    Yields:
        Session: A SQLAlchemy database session.

    Ensures the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_db_and_tables():
    """
    Creates the database and all tables defined in the SQLAlchemy models.

    This function is typically called during application startup to ensure
    the database schema is initialized.
    """
    Base.metadata.create_all(bind=engine)
    print("Database and tables created successfully.")