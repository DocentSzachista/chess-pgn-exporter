"""Database operations module."""
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

import motor.motor_asyncio
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated
from pymongo import ReturnDocument

PyObjectId = Annotated[str, BeforeValidator(str)]

class PGNGame(BaseModel):
    Event: str
    Site: str
    Date: str
    Round: str
    White: str
    Black: str
    Result: str
    Opening: str
    moves: str


class PGNGamesCollection(BaseModel):
    games: List[PGNGame]

class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    studies: Dict[str, List[PGNGame]] | None = {}
    standalone_games: List[PGNGame] | None = []
    lichess_key: str | None = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    password_confirmed: str


MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.pgns

pgn_collection = database.get_collection("pgn_collection")

filter_username_query = lambda username: {"username": username}


def validate_output_decorator(db_operation_func):
    
    async def validator(*args, **kwargs):
        row_edited = await db_operation_func(*args, **kwargs)
        if row_edited.matched_count == 1:
            return True
        return False
    
    return validator 


async def create_new_user(user: UserInDB):
    await pgn_collection.insert_one(
        user.model_dump(exclude=["_id", "id"])
    )


async def check_username(username: str):
    count = await pgn_collection.count_documents(filter_username_query(username))
    if count != 0:
        return True
    else:
        return False


async def retrieve_user(username: str) -> UserInDB:
    user = await pgn_collection.find_one(
        filter_username_query(username), 
        {"_id": 0, "studies": 0, "standalone_games": 0}
    )
    return UserInDB(**user)


@validate_output_decorator
async def update_lichess_token(username: str, token: str):
    return await pgn_collection.update_one(filter_username_query(username), {"$set":{"lichess_key": token}}) 


async def add_new_study(username: str, study_name: str, study_games: PGNGamesCollection):
    return await pgn_collection.find_one_and_update(
        filter_username_query(username), {"$set": {f"studies.{study_name}": study_games}}, 
    )


@validate_output_decorator
async def add_game(username: str, game: PGNGame, study: str | None = None):
    if study:
        return await pgn_collection.update_one(
            filter_username_query(username), {"$push": {f"studies.{study}": game}}, 
        )
    return await pgn_collection.update_one(
            filter_username_query(username), {"$push": {f"standalone_games": game.model_dump_json()}}, 
        )


@validate_output_decorator
async def update_game_moves(username: str, index: int, updated_data: PGNGame, study: str | None = None):
    if study: 
        return await pgn_collection.update_one(
            filter_username_query(username), {"$set": {f"studies.{study}.{index}": updated_data.model_dump_json()}},
        )
    return await pgn_collection.update_one(
            filter_username_query(username), {"$set": {f"standalone_games.{index}": updated_data.model_dump_json()}}, 
        )
    

@validate_output_decorator
async def remove_study(username: str, study: str):
    return await pgn_collection.update_one(
        filter_username_query(username), {"$unset": {f"studies.{study}": 1}}
    )


@validate_output_decorator
async def remove_game(username: str, index: int, study: str | None = None ):
    if study: 
        return await pgn_collection.update_one(
            filter_username_query(username), {"$unset": {f"studies.{study}.{index}": 1}},
        )
    else:
        return  await pgn_collection.update_one(
            filter_username_query(username), {"$unset": {f"standalone_games.{index}": 1}}, 
        )


async def get_user_games(username: str, study: str | None = None):
    if study: 
        return await pgn_collection.find_one(filter_username_query(username),  {"_id": 0, f"studies.{study}": 1, })
    return await pgn_collection.find_one(filter_username_query(username),  {"_id": 0, "standalone_games": 1, })


async def get_user_studies(username: str):
    return await pgn_collection.find_one(filter_username_query(username),  {"_id": 0, f"studies": 1, })

