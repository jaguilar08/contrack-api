from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from models.contract import ContractDetails, ContractIn, ContractOverview
from models.mongo import PyObjectId
from pymongo.database import Database
from utils import responses
from utils.functions import retrieve_contracts

router = APIRouter(
    prefix="/contracts", tags=["contracts"], dependencies=[Depends(auth)]
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_contract(
    contract: ContractIn,
    current_group=Depends(group_parameters),
    db: Database = Depends(get_db)
) -> JSONResponse:
    # verify if the category_id and responsible_id exists
    category = db.categories.find_one(
        {"_id": contract.category_id}, {"_id": 1})
    responsible = db.responsibles.find_one(
        {"_id": contract.responsible_id}, {"_id": 1})
    if category is None or responsible is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Invalid category or responsible")

    contract_data = {
        **current_group,
        **contract.dict(exclude={"extra_fields"})
    }
    # flatten the extra_fields array into a dictionary
    if contract.extra_fields:
        extra_fields = {
            field.field_code: field.details.field_value for field in contract.extra_fields}
        contract_data.update(extra_fields)
    db.contracts.insert_one(contract_data)
    return responses.success_ok()


@router.get("/", response_model=list[ContractOverview])
def list_contracts(current_group=Depends(group_parameters), db: Database = Depends(get_db)):
    pipeline = [
        {
            '$match': {
                **current_group
            }
        }, {
            '$lookup': {
                'from': 'responsibles',
                'localField': 'responsible_id',
                'foreignField': '_id',
                'as': 'responsible_obj'
            }
        }, {
            '$unwind': {
                'path': '$responsible_obj'
            }
        }, {
            '$lookup': {
                'from': 'categories',
                'localField': 'category_id',
                'foreignField': '_id',
                'as': 'category_obj'
            }
        }, {
            '$unwind': {
                'path': '$category_obj'
            }
        }, {
            '$project': {
                '_id': 1,
                'group_code': 1,
                'dealer_code': 1,
                'contractor_name': 1,
                'category': '$category_obj.name',
                'periodicity': 1,
                'type': 1,
                'value': 1,
                'effective_date': 1,
                'responsible': '$responsible_obj.name',
                'contract_status': 1
            }
        }
    ]
    contracts = db.contracts.aggregate(pipeline)
    return list(contracts)


@router.get("/{id}", response_model=ContractDetails)
def get_contract_details(id: PyObjectId, db: Database = Depends(get_db)):
    pipeline = [
        {
            '$match': {
                '_id': id
            }
        }, {
            '$project': {
                'contractor_name': 0,
                'category_id': 0,
                'periodicity': 0,
                'type': 0,
                'value': 0,
                'effective_date': 0,
                'responsible_id': 0,
                'contract_status': 0
            }
        }, {
            '$project': {
                'group_code': 1,
                'dealer_code': 1,
                'extra_fields': {
                    '$filter': {
                        'input': {
                            '$objectToArray': '$$ROOT'
                        },
                        'cond': {
                            '$not': {
                                '$in': [
                                    '$$this.k', [
                                        '_id', 'dealer_code', 'group_code'
                                    ]
                                ]
                            }
                        }
                    }
                }
            }
        }, {
            '$unwind': {
                'path': '$extra_fields'
            }
        }, {
            '$lookup': {
                'from': 'contract_fields',
                'let': {
                    'group_code': '$group_code',
                    'dealer_code': '$dealer_code',
                    'key': '$extra_fields.k',
                    'value': '$extra_fields.v'
                },
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {
                                        '$eq': [
                                            '$field_code', '$$key'
                                        ]
                                    }, {
                                        '$eq': [
                                            '$group_code', '$$group_code'
                                        ]
                                    }, {
                                        '$eq': [
                                            '$dealer_code', '$$dealer_code'
                                        ]
                                    }
                                ]
                            }
                        }
                    }, {
                        '$project': {
                            '_id': 0,
                            'group_code': 0,
                            'dealer_code': 0
                        }
                    }, {
                        '$addFields': {
                            'field_value': '$$value'
                        }
                    }
                ],
                'as': 'field_objs'
            }
        }, {
            '$unwind': {
                'path': '$field_objs'
            }
        }, {
            '$group': {
                '_id': '$_id',
                'extra_fields': {
                    '$push': '$field_objs'
                }
            }
        }
    ]
    result = db.contracts.aggregate(pipeline)
    if not result._has_next():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contract not found")

    extra_fields = next(result)["extra_fields"]
    contract_overview = retrieve_contracts(db, {"_id": id})[0]
    return ContractDetails(**contract_overview.dict(), extra_fields=extra_fields)
