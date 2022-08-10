from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import (authentication, categories, contract_fields, contracts,
                    dashboard, files, responsibles)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authentication.router)
app.include_router(responsibles.router)
app.include_router(categories.router)
app.include_router(contract_fields.router)
app.include_router(contracts.router)
app.include_router(files.router)
app.include_router(dashboard.router)


@ app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "Welcome to ConTrack!"}
