from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from models.mongo import MongoModel

BlockedFields = {"contractor_name", "periodicity", "type", "value", "effective_date",
                 "contract_status", "category_id", "responsible_id", "category", "responsible", "extra_fields", "path"}
FieldStatus = Literal["required", "additional"]
FieldType = Literal["text", "email", "phone",
                    "currency", "number", "toggle", "date"]


class ContractFieldIn(BaseModel):
    """Input data for a new Contract Field"""
    field_label: str
    field_status: FieldStatus
    field_type: FieldType


class ContractFieldOut(MongoModel):
    """Represents the Contract Field in the Mongo database"""
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


class DateValue(BaseModel):
    field_type: Literal["date"]
    field_value: datetime


class ContractFieldValueIn(BaseModel):
    """Represents the data that a field can save"""
    field_code: str
    details: TextValue | IntegerValue | BooleanValue | DateValue


class ContractFieldValueOut(BaseModel):
    field_label: str
    field_status: FieldStatus
    field_type: FieldType
    field_code: str
    field_value: str | bool | int | datetime
