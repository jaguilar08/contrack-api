import re

from database import MongoCon
from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, HTTPException, status
from models.contract_field import (BlockedFields, ContractFieldIn,
                                   ContractFieldOut, ContractFieldUpdate)
from pymongo import ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from utils import responses

router = APIRouter(prefix="/contract_fields",
                   tags=["contract_fields"], dependencies=[Depends(auth)])


@router.on_event("startup")
def router_setup() -> None:
    """Setup the unique index for the Mongo database"""
    with MongoCon() as db:  # can not use dependencies on event handlers
        db.contract_fields.create_index(
            [("group_code", 1), ("dealer_code", 1), ("field_code", 1)], unique=True
        )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ContractFieldOut
)
def create_contract_field(
    contract_field: ContractFieldIn,
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Create a new contract field for a given group"""
    contract_field_data = {
        **current_group,
        **contract_field.dict(),
        "field_code": snake_case(contract_field.field_label)
    }
    if contract_field_data["field_code"] in BlockedFields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Blocked field_code")
    try:
        new_contract_field = db.contract_fields.insert_one(contract_field_data)
    except DuplicateKeyError:
        # if the insertion violates the predefined index
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate code for {current_group['dealer_code']}"
        )
    created_contract_field = db.contract_fields.find_one(
        {"_id": new_contract_field.inserted_id}
    )
    return created_contract_field


@router.get("/", response_model=list[ContractFieldOut])
def list_contract_fields(
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Get all the contract fields for a given group"""
    contract_fields = db.contract_fields.find(current_group)
    return list(contract_fields)


# @router.get("/global_fields", response_model=list[GlobalFieldOut])
# def list_global_contract_fields(db: Database = Depends(get_db)):
#     """Get all of the contract fields that do not require a current group"""
#     global_fields = db.global_fields.find({})
#     return list(global_fields)


@router.post("/{field_code}", response_model=dict)
def update_field_status(
    field_code: str,
    field_update: ContractFieldUpdate,
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Update the field_status of a given contract field"""
    query = {**current_group, "field_code": field_code}
    contract_field = db.contract_fields.find_one_and_update(
        query, {"$set": field_update.dict()}, return_document=ReturnDocument.AFTER
    )
    if contract_field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Field does not exist")
    return responses.success_ok()


@router.get("/init_group_fields", response_model=dict)
def init_group_fields(
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Initializes the contract fields of a new group at the moment of installation"""
    global_fields = db.global_fields.find(
        {}, {**current_group, "field_label": 1, "field_code": 1, "field_type": 1, "field_status": "additional"})
    try:
        _ = db.contract_fields.insert_many(
            list(global_fields))
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "This group has already been initialized")
    return responses.success_ok()


def snake_case(s: str):
    return "_".join(
        re.sub(
            "([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1", s.replace("-", " "))
        ).split()
    ).lower()
