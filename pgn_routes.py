from fastapi import APIRouter, Security, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader
import berserk
import uvicorn
import pgn_parser
from auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])

api_key_header = APIKeyHeader(name="lichess-token")
parser = pgn_parser.ChessGame()


def prepare_session(token: str) -> berserk.Client:
    session = berserk.TokenSession(token)
    client = berserk.Client(session)
    return client

@router.get("/import/Lichess/all")
async def import_all_studies(username: str, token = Depends(api_key_header)):
    lichess_client = prepare_session(token)
    try: 
        pgns = lichess_client.studies.export_by_username(username)
        return parser.import_user_lichess(pgns)
    except:
        raise HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")


@router.get("/import/Lichess/{study_id}")
async def import_study(study_id: int, token = Depends(api_key_header)):
    lichess_client = prepare_session(token)
    try:
        pgns = lichess_client.studies.export(study_id)

    except:
        raise HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")


@router.post("/import/file")
async def import_pgn_file():
    pass 