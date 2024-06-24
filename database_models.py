from pydantic import BaseModel
from typing import List, Dict




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
    username: str
    email: str | None = None
    disabled: bool | None = None
    studies: Dict[str, PGNGamesCollection] | None = None
    standalone_games: PGNGamesCollection | None = None

class UserInDB(User):
    hashed_password: str
