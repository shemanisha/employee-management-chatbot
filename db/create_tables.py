import asyncio

from db.base import Base
from db.session import engine

# Import models so SQLAlchemy knows about all tables
import models


async def create_tables():

    # Open connection to PostgreSQL
    async with engine.begin() as connection:

        # Create all tables
        await connection.run_sync(
            Base.metadata.create_all
        )

    print("Tables created successfully")


# Run async function
asyncio.run(create_tables())