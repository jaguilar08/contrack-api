from const import APPLICATION_CODE
from deps import DGAPI, auth
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from utils import responses

router = APIRouter(tags=["authentication"])


@router.get(
    "/one_authentication"
)
def one_authentication(dgapi: DGAPI = Depends()):
    response = dgapi.post(
        "one_authentication",
        {"application_code": APPLICATION_CODE},
        {'content-type': "application/json"}

    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@router.get("/logout")
def logout(dgapi: DGAPI = Depends()):
    response = dgapi.get("logout")
    return JSONResponse(status_code=response.status_code, content=response.json())


@router.get("/is_authorized", dependencies=[Depends(auth)])
def is_authorized():
    return responses.success_ok()
