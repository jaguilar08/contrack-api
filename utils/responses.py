from fastapi import status
from fastapi.responses import JSONResponse


def success_ok():
    """Success message"""
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "success"})
