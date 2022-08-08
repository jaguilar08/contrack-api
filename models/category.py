from pydantic import BaseModel

from models.mongo import MongoModel


class CategoryIn(BaseModel):
    name: str


class CategoryOut(MongoModel):
    name: str
