from models.contract import ContractIn, ContractOverview
from pymongo.database import Database


def retrieve_contracts(db: Database, query: dict) -> list[ContractOverview]:
    pipeline = [
        {
            '$match': query
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
    result = db.contracts.aggregate(pipeline)
    return [ContractOverview(**contract) for contract in list(result)]


def build_contract_data(contract_in: ContractIn, current_group: dict = {}) -> dict:
    """
    Takes a ContractIn model and flattens the data into a dict so it can be
    inserted into the database.
    """
    contract_data = {
        **current_group,
        **contract_in.dict(exclude={"extra_fields"})
    }
    # flatten the extra_fields array into a dictionary
    if contract_in.extra_fields:
        extra_fields = {
            field.field_code: field.details.field_value for field in contract_in.extra_fields}
        contract_data.update(extra_fields)
    return contract_data
