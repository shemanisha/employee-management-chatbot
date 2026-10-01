from sqlalchemy.orm import DeclarativeBase



# All database models will inherit from this base class

class Base(DeclarativeBase):
    """Base class for all models."""
    pass