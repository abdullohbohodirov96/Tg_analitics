"""
SQLAlchemy Base class — Separated to avoid circular imports.
"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Barcha modellar uchun base class"""
    pass
