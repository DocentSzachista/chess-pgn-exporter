"""PGN related endpoints module."""
import logging
from typing import Annotated

import berserk
import pgn_parser
from database_models import User, add_new_study, update_lichess_token
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from pymongo.errors import OperationFailure

from .auth import get_current_active_user

router = APIRouter(
    dependencies=[Depends(get_current_active_user)]
)

parser = pgn_parser.ChessGame()


def prepare_session(token: str) -> berserk.Client:
    session = berserk.TokenSession(token)
    client = berserk.Client(session)
    return client


@router.get("/import/Lichess/all")
async def import_all_studies(username: str, user: Annotated[User, Depends(get_current_active_user)]):
    lichess_client = prepare_session(user.lichess_key)
    try: 
        pgns = lichess_client.studies.export_by_username(username)
        parsed_pgns = parser.import_user_lichess(pgns)
        for keys in parsed_pgns.keys():
            await add_new_study(user.username, keys, parsed_pgns[keys])
        return parsed_pgns
    except OperationFailure as e:
        logging.debug(e.with_traceback())
        raise HTTPException(413, "User studies are too big. Uploaded only part of it")
    except:
        logging.debug("Permission to study denied")
        raise HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")


@router.get("/import/Lichess/{study_id}")
async def import_study(study_id: int, user: Annotated[User, Depends(get_current_active_user)]):
    lichess_client = prepare_session(user.lichess_key)
    try:
        pgns = lichess_client.studies.export(study_id)
        parsed_pgns = parser.import_user_lichess(pgns)
        await add_new_study(user.username, study_id, study_games=parsed_pgns)
        return {study_id: parsed_pgns}
    except:
        raise HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")


@router.post("/import/file")
async def import_pgn_file(file: UploadFile):
    if file.content_type != "application/octet-stream":
        raise HTTPException(422, "Invalid input type")
    content = await file.read()
    print(content)
    return {"filename": file.content_type}


@router.put("/updateToken")
async def update_token(token: str, user: Annotated[User, Depends(get_current_active_user)]):
    updated_succesfully = await update_lichess_token(user.username, token)
    if updated_succesfully:
        user.lichess_key = token
        return Response(status_code=200)
    return HTTPException(400, "Something bad happened during update")