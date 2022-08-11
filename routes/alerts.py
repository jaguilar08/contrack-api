from datetime import datetime

from dateutil.relativedelta import relativedelta
from deps import get_db, group_parameters
from fastapi import APIRouter, Depends, Query
from models.contract import ContractOverview
from pymongo.database import Database
from utils.functions import retrieve_contracts

router = APIRouter(prefix="/alerts",
                   tags=["alerts"], dependencies=[Depends(get_db)])


@router.get("/", response_model=list[ContractOverview])
def get_alerts(days_filter: int = Query(gt=0),
               current_group: dict = Depends(group_parameters),
               db: Database = Depends(get_db)):
    today_delta = datetime.today() + relativedelta(days=days_filter)
    contracts = retrieve_contracts(db, {"$and": [
        current_group,
        {"due_date": {"$lte": today_delta}},
        {"contract_status": "active"}
    ]})
    return contracts
