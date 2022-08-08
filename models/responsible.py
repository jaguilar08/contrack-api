from pydantic import BaseModel

from models.mongo import MongoModel


class ResponsibleIn(BaseModel):
    name: str


class ResponsibleOut(MongoModel):
    name: str
