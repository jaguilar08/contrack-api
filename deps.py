from typing import Generator

import jwt
from fastapi import Depends, Header, HTTPException, Request, status

from database import MongoCon
from dgapi import DGAPI as DGAPIBase
from models.credentials import Credentials


class DGAPI(DGAPIBase):
    """Return API object"""

    def __init__(self, request: Request):
        self.headers = dict(request.headers)


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
