import os
from typing import Any, BinaryIO, Generator

import boto3
import jwt
from botocore.exceptions import ClientError
from fastapi import Depends, Header, HTTPException, Request, status

from const import AWS_S3_BUCKET_NAME, AWS_S3_ROOT_FOLDER
from database import MongoCon
from dgapi import DGAPI as DGAPIBase
from models.credentials import Credentials


class DGAPI(DGAPIBase):
    """Return API object"""

    def __init__(self, request: Request):
        self.headers = dict(request.headers)


class AWSS3:
    """Logic for uploading and downloading AWS S3 files"""
    BUCKET_NAME = AWS_S3_BUCKET_NAME
    ROOT_FOLDER = AWS_S3_ROOT_FOLDER

    def __init__(self):
        self.client = boto3.client("s3")

    def upload_fileobj(self, file: BinaryIO, object_name: str, ExtraArgs: dict | None = None) -> Any:
        """Upload a file-like object to an S3 bucket

        Args:
            file (BinaryIO): The file-like object to upload
            object_name (str): S3 object name

        Returns:
            Any: The S3 client response

        Raises:
            ClientError: The S3 service responded with an error
        """
        return self.client.upload_fileobj(
            file, self.BUCKET_NAME, os.path.join(
                self.ROOT_FOLDER, object_name), ExtraArgs=ExtraArgs)

    def tag_object(self, object_name: str, tags: dict[str, str]) -> Any:
        """Put key-value tags onto the specified object 

        Args:
            object_name (str): S3 object name
            tags (dict[str, str]): List of key-value tags

        Returns:
            Any: S3 client response

        Raises:
            ClientError: The S3 service responded with an error
        """
        return self.client.put_object_tagging(
            Bucket=self.BUCKET_NAME,
            Key=os.path.join(self.ROOT_FOLDER, object_name),
            Tagging={
                "TagSet": self.get_tag_set(tags)
            }
        )

    def move_object(self, original_path: str, new_path: str) -> None:
        original_path = os.path.join(self.ROOT_FOLDER, original_path)
        # raises exception if file does not exist
        self.client.head_object(Bucket=self.BUCKET_NAME, Key=original_path)
        # copy the original file to the new location
        copy_source = {
            "Bucket": self.BUCKET_NAME,
            "Key": original_path
        }
        new_path = os.path.join(self.ROOT_FOLDER, new_path)
        self.client.copy_object(Bucket=self.BUCKET_NAME, CopySource=copy_source,
                                Key=new_path)
        # delete the original file
        self.client.delete_object(Bucket=self.BUCKET_NAME,
                                  Key=original_path)

    def get_file(self, filepath: str) -> dict:
        filepath = os.path.join(self.ROOT_FOLDER, filepath)
        try:
            response = self.client.head_object(
                Bucket=self.BUCKET_NAME, Key=filepath)
        except ClientError:
            return {}
        return {
            "path": filepath,
            "size": response["ContentLength"]
        }

    @classmethod
    def get_tag_set(cls, tags: dict[str, str]) -> list[dict[str, str]]:
        return [{"Key": key, "Value": value} for key, value in tags.items()]


def get_db() -> Generator:
    """Return the MongoDB database"""
    with MongoCon() as db:
        yield db


def auth(
    security_token: str = Header(),
    dgapi: DGAPI = Depends()
) -> Credentials:
    """
    Check the request's token and verifies if the client is authenticated.
    If that is the case, then the credentials are returned for future use.
    """
    try:
        data = jwt.decode(security_token, "@3!f3719em$893&",
                          ["HS256"])  # token decode
    except Exception:  # jwt.ExpiredSignatureError
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access"
        )
    else:  # valid token
        # check if authorized
        response = dgapi.get("valid_token")
        if response.status_code != 200:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                                detail="Unauthorized access")
        # return credentials if needed
        return Credentials(
            data["user_id"],
            data["user_application_id"],
            data["name"],
            data.get("email", None),
            data.get("security_token", None)
        )


async def group_parameters(
    current_group: str = Header(), current_dealer: str = Header()
) -> dict[str, str]:
    """Get the current group and dealer code from the request headers"""
    return {"group_code": current_group, "dealer_code": current_dealer}
