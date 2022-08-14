import heapq
import math
from datetime import datetime
from operator import itemgetter
from turtle import update

from dateutil.relativedelta import relativedelta
from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.contract import ContractType
from models.dashboard import (AnnualDashboardOut, MonthlyDashboardOut,
                              OldestDateOut)
from pymongo.database import Database

router = APIRouter(prefix="/dashboard",
                   tags=["dashboard"], dependencies=[Depends(auth)])


@router.get("/monthly", response_model=MonthlyDashboardOut)
def get_monthly_data(month: int = Query(ge=1, le=12), year: int = Query(),
                     type: ContractType = Query(), current_group=Depends(group_parameters),
                     db: Database = Depends(get_db)):
    try:
        date_filter = datetime.strptime(f"{month} {year}", "%m %Y")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filter")
    date_filter_next = date_filter + relativedelta(months=1)
    pipeline = [
        {
            '$match': {
                '$and': [
                    current_group,
                    {
                        'effective_date': {
                            '$lt': date_filter_next
                        }
                    }, {
                        'due_date': {
                            '$gte': date_filter
                        }
                    }, {
                        'contract_status': {
                            '$nin': [
                                'inactive'
                            ]
                        }
                    }, {
                        'type': type
                    }
                ]
            }
        }, {
            '$project': {
                'value': 1,
                'responsible_id': 1,
                'category_id': 1,
                'periodicity': 1,
                'status': 1,
                'contract_status': 1
            }
        }, {
            '$lookup': {
                'from': 'categories',
                'localField': 'category_id',
                'foreignField': '_id',
                'as': 'category_objs'
            }
        }, {
            '$unwind': {
                'path': '$category_objs'
            }
        }, {
            '$lookup': {
                'from': 'responsibles',
                'localField': 'responsible_id',
                'foreignField': '_id',
                'as': 'responsible_objs'
            }
        }, {
            '$unwind': {
                'path': '$responsible_objs'
            }
        }, {
            '$group': {
                '_id': 'database',
                'quantity': {
                    '$sum': 1
                },
                'total_value': {
                    '$sum': '$value'
                },
                'average_value': {
                    '$avg': '$value'
                },
                'contracts': {
                    '$push': {
                        'value': '$value',
                        'status': '$contract_status',
                        'periodicity': '$periodicity',
                        'responsible': '$responsible_objs.name',
                        'category': '$category_objs.name'
                    }
                }
            }
        }
    ]
    result = db.contracts.aggregate(pipeline)
    dashboard = next(result, {})
    if not dashboard:
        return MonthlyDashboardOut()
    by_category = {}
    by_responsible = {}
    by_periodicity = {}
    for contract in dashboard["contracts"]:
        def update_group(group: dict, key: str):
            if not group.get(key, False):
                group[key] = {
                    "quantity": 0,
                    "total_value": 0.0
                }
            group[key]["quantity"] += 1
            group[key]["total_value"] += contract["value"]
        update_group(by_category, contract["category"])
        update_group(by_responsible, contract["responsible"])
        update_group(by_periodicity, contract["periodicity"])

    by_category = [{"key": k, **v} for k, v in
                   heapq.nlargest(10, by_category.items(),
                                  key=lambda kv: kv[1]["total_value"])]
    by_responsible = [{"key": k, **v} for k, v in
                      heapq.nlargest(10, by_responsible.items(),
                                     key=lambda kv: kv[1]["total_value"])]
    by_periodicity = [{"key": k, **v} for k, v in by_periodicity.items()]

    for group in (by_category, by_responsible, by_periodicity):
        for item in group:
            item["average_value"] = round(
                item["total_value"] / item["quantity"], 2)

    # get inactive contracts
    pipeline = [
        {
            '$match': {
                '$and': [
                    current_group,
                    {'contract_status': 'inactive'},
                ]
            }
        }, {
            '$group': {
                '_id': 'dashboard',
                'quantity': {
                    '$sum': 1
                },
                'total_value': {
                    '$sum': '$value'
                }
            }
        }
    ]
    result = db.contracts.aggregate(pipeline)
    inactive_data = next(result, {})
    if not inactive_data:
        inactive_data = {
            "quantity": 0,
            "total_value": 0.0
        }
    else:
        inactive_data = {
            "quantity": inactive_data["quantity"],
            "total_value": inactive_data["total_value"]
        }
    return {
        "quantity": dashboard["quantity"],
        "total_value": dashboard["total_value"],
        "average_value": round(dashboard["average_value"], 2),
        "by_category": by_category,
        "by_responsible": by_responsible,
        "by_periodicity": by_periodicity,
        "inactive_quantity": inactive_data["quantity"],
        "inactive_total_value": inactive_data['total_value']
    }


@ router.get("/monthly/get_oldest", response_model=OldestDateOut)
def get_oldest_date(current_group: dict[str, str] = Depends(group_parameters), db: Database = Depends(get_db)):
    contract = db.contracts.find(
        {**current_group, "contract_status": {"$nin": ["inactive"]}}, {"_id": 0, "effective_date": 1, "due_date": 1}).sort("effective_date").limit(1)
    contract = next(contract, {})
    if not contract:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No contracts found")
    return {
        "year": contract["effective_date"].year,
        "month": contract["effective_date"].month
    }


@router.get("/annual", response_model=AnnualDashboardOut)
def get_annual_data(year: int, type: ContractType,
                    current_group=Depends(group_parameters),
                    db: Database = Depends(get_db)):
    try:
        date_filter_start = datetime(year, 1, 1)
        date_filter_end = datetime(year, 12, 31, 23, 59, 59)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid year")
    pipeline = [
        {
            '$match': {
                '$and': [
                    current_group,
                    {
                        'contract_status': 'active'
                    }, {
                        'effective_date': {
                            '$lte': date_filter_end
                        }
                    }, {
                        'effective_date': {
                            '$gte': date_filter_start
                        }
                    }, {
                        'type': type
                    }
                ]
            }
        }, {
            '$project': {
                '_id': 0,
                'effective_date': 1,
                'value': 1,
                'periodicity': 1,
                'due_date': 1
            }
        }
    ]
    result = db.contracts.aggregate(pipeline)
    if not next(result, {}):
        AnnualDashboardOut()
    """
    result structure:
        periodicity: str
        value: float
        effective_date: datetime
        due_date: datetime
    """
    contracts = iter(result)
    by_month = {str(i): {"quantity": 0, "total_value": 0.0}
                for i in range(1, 13)}
    periodicity = ("monthly", "bimonthly", "quarterly",
                   "biannually", "annually")
    by_periodicity = {p: {"quantity": 0, "total_value": 0.0}
                      for p in periodicity}
    ranges = ((0, 1000), (1001, 5000), (5001, 10000), (10001, "inf"))
    by_value_range = {
        f"{a} - {b}": 0 for a, b in ranges
    }
    for contract in contracts:
        def update_group(group: dict, key: str):
            group[key]["quantity"] += 1
            group[key]["total_value"] += contract["value"]
        update_group(by_month, str(contract["effective_date"].month))
        update_group(by_periodicity, contract["periodicity"])
        # update by_value_range
        int_value = math.ceil(contract["value"])
        for l, h in ranges:
            if h == "inf":
                by_value_range[f"{l} - {h}"] += 1
                break
            else:
                if int_value in range(l, h+1):
                    by_value_range[f"{l} - {h}"] += 1
                    break
    return {
        "by_month": [{"key": k, **v} for k, v in by_month.items()],
        "by_periodicity": [{"key": k, **v} for k, v in by_periodicity.items()],
        "by_value_range_qty": [{"key": k, "quantity": v} for k, v in by_value_range.items()]
    }
