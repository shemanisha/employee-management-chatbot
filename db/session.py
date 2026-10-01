from sqlalchemy.ext.asyncio import (create_async_engine, async_sessionmaker)
from core.config import settings



# Create connection engine for PostgresSql
engine=create_async_engine(settings.database_url, echo=False)


#This will create database session for us 
AsyncSessionLocal=async_sessionmaker(bind=engine, expire_on_commit=False)



async def get_db():

    async with AsyncSessionLocal as session:
        try:
            # Give session to FastApi endpoint
            yield session

        except Exception:
            # If something fails, undo current transaction
            await session.rollback()

            # Send error upward
            raise

