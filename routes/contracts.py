from deps import auth, get_db, group_parameters
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from models.contract import ContractDetails, ContractIn, ContractOverview
from models.mongo import PyObjectId
from pymongo.database import Database
from utils import responses
from utils.functions import build_contract_data, retrieve_contracts

router = APIRouter(
    prefix="/contracts", tags=["contracts"], dependencies=[Depends(auth)]
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ContractOverview)
def create_contract(
    contract: ContractIn,
    current_group=Depends(group_parameters),
    db: Database = Depends(get_db),
):
    # verify if the category_id and responsible_id exists
    category = db.categories.find_one(
        {"_id": contract.category_id}, {"_id": 1})
    if category is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Invalid category")
    responsible = db.responsibles.find_one(
        {"_id": contract.responsible_id}, {"_id": 1})
    if responsible is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Invalid responsible")

    contract_data = build_contract_data(contract, current_group)
    new_contract = db.contracts.insert_one(contract_data)
    new_contract = retrieve_contracts(db, {"_id": new_contract.inserted_id})
    return new_contract[0]


@router.get("/", response_model=list[ContractOverview])
def list_contracts(current_group=Depends(group_parameters), db: Database = Depends(get_db)):
    return retrieve_contracts(db, current_group)


@router.get("/search/{query}", response_model=list[ContractOverview])
def search_contract(query: str, db: Database = Depends(get_db), current_group=Depends(group_parameters)):
    return retrieve_contracts(db, {
        '$and': [
            {**current_group},
            {'contractor_name': {'$regex': query}}
        ]
    })


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


@router.put("/{id}", response_model=ContractOverview)
def update_contract(id: PyObjectId, contract: ContractIn, db: Database = Depends(get_db)):
    # verify if the category_id and responsible_id exists
    category = db.categories.find_one(
        {"_id": contract.category_id}, {"_id": 1})
    if category is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Invalid category")
    responsible = db.responsibles.find_one(
        {"_id": contract.responsible_id}, {"_id": 1})
    if responsible is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Invalid responsible")

    updated_contract_data = build_contract_data(contract)
    updated_contract = db.contracts.find_one_and_update({"_id": id}, {
        "$set": updated_contract_data
    })
    if not updated_contract:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contract not found")

    return retrieve_contracts(db, {"_id": id})[0]


@router.delete("/{id}")
def delete_contract(id: PyObjectId, db: Database = Depends(get_db)) -> JSONResponse:
    """Delete a contract using its id"""
    result = db.contracts.delete_one({"_id": id})
    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contract not found")
    return responses.success_ok()
