from pydantic import BaseModel

from models.mongo import MongoModel


class ResponsibleIn(BaseModel):
    """The input data for a new Responsible"""
    name: str


class ResponsibleOut(MongoModel):
    """Represents the Responsible in the Mongo database"""
    name: str
