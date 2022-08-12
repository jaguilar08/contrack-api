from database import MongoCon
from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, HTTPException, status
from models.category import CategoryIn, CategoryOut
from models.mongo import PyObjectId
from pymongo import ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

router = APIRouter(
    prefix="/categories", tags=["categories"], dependencies=[Depends(auth)]
)


@router.on_event("startup")
def router_setup() -> None:
    """Setup the unique index for the Mongo database"""
    with MongoCon() as db:  # can not use dependencies on event handlers
        db.categories.create_index(
            [("group_code", 1), ("dealer_code", 1), ("name", 1)], unique=True
        )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CategoryOut)
def create_category(
    category: CategoryIn,
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Create a new category for the current group"""
    category_data = {**current_group, **category.dict()}
    try:
        new_category = db.categories.insert_one(category_data)
    except DuplicateKeyError:
        # if the insertion violates the predefined index
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"Duplicate na for {current_group['dealer_code']}")
    created_category = db.categories.find_one(
        {"_id": new_category.inserted_id})
    return created_category


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    current_group: dict = Depends(group_parameters),
    db: Database = Depends(get_db)
):
    """Get a list of all categories for the specified group"""
    categories = db.categories.find(current_group)
    return list(categories)


@router.put("/{id}", response_model=CategoryOut)
def update_category(
    id: PyObjectId,
    category: CategoryIn,
    db: Database = Depends(get_db)
):
    try:
        updated_category = db.categories.find_one_and_update(
            {"_id": id}, {"$set": category.dict()}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Duplicate name for current group")
    if updated_category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="Category not found")
    return updated_category
