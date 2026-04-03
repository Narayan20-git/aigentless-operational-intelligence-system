
from beanie import Document
class User(Document):
    email:str
    hashed_password:str
    is_active: bool = True
