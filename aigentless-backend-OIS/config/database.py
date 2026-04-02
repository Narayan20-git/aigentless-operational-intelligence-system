
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user_model import User

def get_client():
    return AsyncIOMotorClient('mongodb://localhost:27017')

async def init_db():
    client = get_client()
    await init_beanie(database=client.aigentless, document_models=[User])
