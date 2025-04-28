#!/usr/bin/env python3
"""
This module initializes the FastAPI application, configures logging, and sets
up the application lifespan. It includes routers for handling institution and
file-related endpoints and ensures the database is created on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import create_db_and_tables
from .routers import institution, files
import logging
import sys


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    This function is executed during the startup and shutdown of the FastAPI
    application. It configures logging and ensures the database and tables
    are created on application startup.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None
    """
    # --- Basic Logging Configuration ---
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )
    log_level = logging.INFO  # Set the desired minimum level (e.g., INFO, DEBUG)

    # --- File Handler ---
    log_file_handler = logging.FileHandler("app.log", mode='a', encoding='utf-8')
    log_file_handler.setFormatter(log_formatter)
    log_file_handler.setLevel(log_level)

    # --- Console Handler ---
    log_console_handler = logging.StreamHandler(sys.stdout)
    log_console_handler.setFormatter(log_formatter)
    log_console_handler.setLevel(log_level)

    # --- Root Logger Configuration ---
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(log_file_handler)
    root_logger.addHandler(log_console_handler)

    # Example log messages
    logger = logging.getLogger("app")
    logger.info("Starting application...")

    # Create database and tables
    await create_db_and_tables()
    yield


# Initialize the FastAPI application
app = FastAPI(lifespan=lifespan)

# Include routers for institution and file endpoints
app.include_router(institution.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
