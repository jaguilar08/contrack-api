from typing import Literal

from pydantic import BaseModel

from models.mongo import MongoModel

FieldStatus = Literal["required", "additional"]
FieldType = Literal["text", "email", "phone",
                    "currency", "number", "toggle", "date"]


class ContractFieldIn(BaseModel):
    field_label: str
    field_status: FieldStatus
    field_type: FieldType


class ContractFieldOut(MongoModel):
    field_label: str
    field_code: str
    field_status: FieldStatus
    field_type: FieldType


class ContractFieldUpdate(BaseModel):
    field_status: FieldStatus


class TextValue(BaseModel):
    field_type: Literal["text", "email"]
    field_value: str


class IntegerValue(BaseModel):
    field_type: Literal["number", "phone"]
    field_value: int


class BooleanValue(BaseModel):
    field_type: Literal["toggle"]
    field_value: bool


class FieldValueIn(BaseModel):
    field_code: str
    details: TextValue | IntegerValue | BooleanValue


class ContractFieldValueOut(BaseModel):
    field_label: str
    field_status: FieldStatus
    field_type: FieldType
    field_code: str
    field_value: str | bool | int
