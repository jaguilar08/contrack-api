from pydantic import BaseModel

from models.mongo import MongoModel


class CategoryIn(BaseModel):
    """The input data for a new Category"""
    name: str


class CategoryOut(MongoModel):
    """Represents the Category in the Mongo database"""
    name: str
