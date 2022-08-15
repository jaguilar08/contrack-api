from database import MongoCon
from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, HTTPException, status
from models.mongo import PyObjectId
from models.responsible import ResponsibleIn, ResponsibleOut
from pymongo import ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

router = APIRouter(
    prefix="/responsibles", tags=["responsibles"], dependencies=[Depends(auth)]
)


@router.on_event("startup")
def router_setup() -> None:
    """Setup the unique index for the Mongo database"""
    try:
        with MongoCon() as db:  # can not use dependencies on event handlers
            db.responsibles.create_index(
                [("group_code", 1), ("dealer_code", 1), ("name", 1)], unique=True
            )
    except:
        pass


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=ResponsibleOut
)
def create_responsible(
    responsible: ResponsibleIn,
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Create a new responsible for the current group"""
    responsible_data = {**current_group, **responsible.dict()}
    try:
        new_responsible = db.responsibles.insert_one(responsible_data)
    except DuplicateKeyError:
        # if the insertion violates the predefined index
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate name for {current_group['dealer_code']}"
        )
    created_responsible = db.responsibles.find_one(
        {"_id": new_responsible.inserted_id}
    )
    return created_responsible


@router.get(
    "/", response_model=list[ResponsibleOut]
)
def list_responsibles(
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Return all of the responsibles for the specified group"""
    responsibles = db.responsibles.find(current_group)
    return list(responsibles)


@router.put("/{id}", response_model=ResponsibleOut)
def update_responsible(
    id: PyObjectId, responsible: ResponsibleIn, db: Database = Depends(get_db)
):
    try:
        updated_responsible = db.responsibles.find_one_and_update(
            {"_id": id}, {"$set": responsible.dict()}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Duplicate name for current group")
    if updated_responsible is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="Responsible not found")
    return updated_responsible
