from datetime import datetime, timedelta
from operator import itemgetter

from dateutil.relativedelta import relativedelta
from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, Query
from models.contract import AlertsContractOverview
from pymongo.database import Database
from utils.functions import retrieve_contracts

router = APIRouter(prefix="/alerts",
                   tags=["alerts"], dependencies=[Depends(auth)])


@router.get("/", response_model=list[AlertsContractOverview])
def get_alerts(days_filter: int = Query(gt=0),
               current_group: dict = Depends(group_parameters),
               db: Database = Depends(get_db)):
    today_delta = datetime.today() + relativedelta(days=days_filter+1)
    contracts = retrieve_contracts(db, {"$and": [
        current_group,
        {"due_date": {"$lt": today_delta}},
        {"contract_status": "active"}
    ]})

    l = []
    for contract in contracts:
        delta = contract.due_date - datetime.today()
        dict_contract = contract.dict()
        dict_contract["days_until_due_date"] = delta.days
        l.append(dict_contract)
    return sorted(l, key=itemgetter("days_until_due_date"))
