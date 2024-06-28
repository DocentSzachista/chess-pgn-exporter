from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import motor.motor_asyncio
from uuid import UUID, uuid4
from pydantic.functional_validators import BeforeValidator
from pydantic import Field
from typing_extensions import Annotated

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
    studies: Dict[str, PGNGamesCollection] | None = None
    standalone_games: PGNGamesCollection | None = None
    lichess_key: str | None = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    password_confirmed: str




# MONGO_DETAILS = "mongodb://root:example@mongo:27017"
MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.pgns

pgn_collection = database.get_collection("pgn_collection")


async def create_new_user(user: UserInDB):
    await pgn_collection.insert_one(
        user.model_dump(exclude=["_id", "id"])
    )


async def check_username(username: str):
    count = await pgn_collection.count_documents({"username": username})
    if count != 0:
        return True
    else:
        return False
    # cursor = pgn_collection.find({}, {"_id": 0})
    # documents = await cursor.to_list(10)
    # documents = []
    # for document in cursor:
    #     documents.append(document)
    # return documents


async def retrieve_user(username: str) -> UserInDB:
    user = await pgn_collection.find_one({"username": username}, {"_id": 0, "studies": 0, "standalone_games": 0})
    return UserInDB(**user)

async def add_new_study(study: Dict[str, PGNGamesCollection]):
    pass 

async def add_game(game: PGNGame, study: str | None = None):
    pass


async def remove_study(study: str):
    pass 


async def remove_game(study: str, index: int):
    pass 


async def update_game_in_study(study: str, index: int, game: PGNGame):
    pass 