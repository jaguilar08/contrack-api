import os
from urllib import parse
from uuid import uuid4

from botocore.exceptions import ClientError
from deps import AWSS3, auth, get_db
from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, status
from models.mongo import PyObjectId
from pydantic import BaseModel
from pymongo.database import Database
from utils.responses import success_ok


class FileCreated(BaseModel):
    path: str


router = APIRouter(
    prefix="/files", tags=["files"], dependencies=[Depends(auth)])


@router.post("/upload", response_model=FileCreated)
def upload_file(file: UploadFile, s3: AWSS3 = Depends()):
    """Upload a file to the S3 bucket"""
    _, ext = os.path.splitext(file.filename)
    filename = f"{uuid4().hex}{ext}"
    filepath = os.path.join("uploads", filename)
    try:
        # Upload the file into the ENV/uploads directory, and tag it as unlinked.
        # Unlinked files are temporary, and are automatically deleted after one day.
        s3.upload_fileobj(file.file, filepath, {
            "ContentType": file.content_type,
            "Tagging": parse.urlencode({"status": "unlinked"})})
    except ClientError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="The S3 service responded with an error")
    return {
        "path": filepath
    }


@router.post("/link_to_contract")
def link_to_contract(filepath: str = Body(), contract_id: PyObjectId = Body(),
                     s3: AWSS3 = Depends(), db: Database = Depends(get_db)):
    contract = db.contracts.find_one({"_id": contract_id})
    if not contract:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="Contract not found")
    if contract.get("path", False):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Contract is linked to another file")
    # check that the file has not already been linked
    found = db.files.find_one({"path": filepath}, {"_id": 1})
    if found is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="File has already been linked")
    filename = os.path.basename(filepath)
    new_path = os.path.join(str(contract_id), filename)

    try:
        s3.move_object(filepath, new_path)
        # mark the file as linked so it does not get automatically deleted
        s3.tag_object(new_path, {"status": "linked"})
    except ClientError as ex:
        if ex.response["Error"]["Code"] == "NoSuchKey":
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                detail="File does not exists")
        raise HTTPException(status.WS_1011_INTERNAL_ERROR,
                            detail="The S3 service responded with an error")
    # create a db entry
    file_info = s3.get_file(new_path)
    db.files.insert_one({
        "contract_id": contract["_id"],
        "path": new_path,
        "filename": filename,
        "size": file_info.get("size", None)
    })
    # add field to contract
    db.contracts.update_one({"_id": contract_id}, {
        "$set": {
            "path": new_path
        }
    })
    return success_ok()


@router.post("/unlink")
def unlink_file(filepath: str = Body(), db: Database = Depends(get_db), s3: AWSS3 = Depends()):
    file = db.files.find_one({"path": filepath})
    if not file:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File not found")
    db.contracts.update_one({"_id": file["contract_id"]}, {
        "$unset": {
            "path": True
        }
    })
    try:
        s3.tag_object(filepath, {"status": "unlinked"})
    except ClientError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "The S3 service returned an error")
    db.files.delete_one({"_id": file["_id"]})
    return success_ok()
