from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Annotated
from fastapi.security import APIKeyHeader
import berserk
import pgn_parser
from .auth import get_current_active_user
from database_models import update_lichess_token, User

router = APIRouter(dependencies=[Depends(get_current_active_user)])

api_key_header = APIKeyHeader(name="lichess-token")
parser = pgn_parser.ChessGame()


def prepare_session(token: str) -> berserk.Client:
    session = berserk.TokenSession(token)
    client = berserk.Client(session)
    return client

@router.get("/import/Lichess/all")
async def import_all_studies(username: str, user = Depends(get_current_active_user)):
    lichess_client = prepare_session(user.lichess_key)
    try: 
        pgns = lichess_client.studies.export_by_username(username)
        return parser.import_user_lichess(pgns)
    except:
        raise HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")


@router.get("/import/Lichess/{study_id}")
async def import_study(study_id: int, user = Depends(get_current_active_user)):
    lichess_client = prepare_session(user.lichess_key)
    try:
        pgns = lichess_client.studies.export(study_id)
        return parser.import_user_lichess(pgns)
    except:
        raise HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")


@router.post("/import/file")
async def import_pgn_file():
    pass 


@router.put("/updateToken")
async def update_token(token: str, user: Annotated[User, Depends(get_current_active_user)]):
    updated_succesfully = await update_lichess_token(user, token)
    if updated_succesfully:
        user.lichess_key = token
        return Response(status_code=200)
    return HTTPException(400, "Something bad happened during update")