import pymongo, os
from config import DB_URL, DB_NAME

dbclient = pymongo.MongoClient(DB_URL)
database = dbclient[DB_NAME]
user_data = database['users']
force_sub_requests = database['force_sub_requests']



async def present_user(user_id : int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id})
    return

async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
        
    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return











async def save_force_sub_request(user_id: int, channel_id: int):
    """Remember that the user submitted a join request (approval is not required)."""
    force_sub_requests.update_one(
        {"_id": int(user_id)},
        {"$set": {"channel_id": int(channel_id), "requested": True}},
        upsert=True,
    )


async def has_force_sub_request(user_id: int, channel_id: int) -> bool:
    """Return True once Telegram has delivered this user's join request."""
    return force_sub_requests.find_one(
        {"_id": int(user_id), "channel_id": int(channel_id), "requested": True}
    ) is not None
