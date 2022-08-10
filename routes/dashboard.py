from datetime import datetime

from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.contract import ContractType
from models.dashboard import DashboardOut
from pymongo.database import Database

router = APIRouter(prefix="/dashboard",
                   tags=["dashboard"], dependencies=[Depends(auth)])


@router.get("/monthly", response_model=DashboardOut)
def get_monthly_data(month: int = Query(ge=1, le=12), year: int = Query(),
                     type: ContractType = Query(), current_group=Depends(group_parameters),
                     db: Database = Depends(get_db)):
    try:
        date_filter = datetime.strptime(f"{month} {year}", "%m %Y")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filter")
    pipeline = [
        {
            '$match': {
                '$and': [
                    current_group,
                    {
                        'effective_date': {
                            '$lte': date_filter
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
        return DashboardOut()
    by_category = {}
    by_responsible = {}
    by_periodicity = {}
    for contract in dashboard["contracts"]:
        def update_group(group: dict, key: str):
            if not group.get(key, False):
                group[key] = {
                    "quantity": 0,
                    "total_value": 0
                }
            group[key]["quantity"] += 1
            group[key]["total_value"] += contract["value"]
        update_group(by_category, contract["category"])
        update_group(by_responsible, contract["responsible"])
        update_group(by_periodicity, contract["periodicity"])

    for group in (by_category, by_responsible, by_periodicity):
        for data in group.values():
            data["average_value"] = data["total_value"] / data["quantity"]

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
        "average_value": dashboard["average_value"],
        "by_category": by_category,
        "by_responsible": by_responsible,
        "by_periodicity": by_periodicity,
        "inactive_quantity": inactive_data["quantity"],
        "inactive_total_value": inactive_data['total_value']
    }
