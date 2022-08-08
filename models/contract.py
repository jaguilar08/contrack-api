from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from models.contract_field import ContractFieldValueOut, FieldValueIn
from models.mongo import MongoModel, PyObjectId

ContractStatus = Literal["active", "inactive"]

ContractPeriodicity = Literal["monthly",
                              "bimonthly", "quarterly", "biannually", "annually"]

ContractType = Literal["liability", "revenue"]


class ContractBase(BaseModel):
    contractor_name: str
    periodicity: ContractPeriodicity
    type: ContractType
    value: float
    effective_date: datetime
    contract_status: ContractStatus


class ContractIn(ContractBase):
    category_id: PyObjectId
    responsible_id: PyObjectId
    extra_fields: list[FieldValueIn] | None


class ContractOverview(MongoModel, ContractBase):
    category: str
    responsible: str


class ContractDetails(MongoModel, ContractBase):
    category: str
    responsible: str
    extra_fields: list[ContractFieldValueOut] | None