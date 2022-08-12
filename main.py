from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes import (alerts, authentication, categories, contract_fields,
                    contracts, dashboard, files, responsibles)

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
app.include_router(alerts.router)


@ app.get("/", tags=["root"])
async def root() -> JSONResponse:
    return JSONResponse(content={"message": "Welcome to ConTrack!"})
