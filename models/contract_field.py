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
