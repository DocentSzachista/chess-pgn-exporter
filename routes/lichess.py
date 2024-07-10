"""PGN related endpoints module."""
import logging
from typing import Annotated

import berserk
from database_models import User, add_new_study, update_lichess_token, PGNGame, update_game_moves, remove_study, remove_game
from dependencies import parser
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from pymongo.errors import OperationFailure

from .auth import get_current_active_user

router = APIRouter(
    prefix="/lichess",
    tags=["lichess"],
    dependencies=[Depends(get_current_active_user)]
)


def prepare_session(token: str) -> berserk.Client:
    session = berserk.TokenSession(token)
    client = berserk.Client(session)
    return client


@router.get("/import/all")
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
        return HTTPException(413, "User studies are too big. Uploaded only part of it")
    except:
        logging.debug("Permission to study denied")
        return HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")


@router.get("/import/{study_id}")
async def import_study(study_id: int, user: Annotated[User, Depends(get_current_active_user)]):
    lichess_client = prepare_session(user.lichess_key)
    try:
        pgns = lichess_client.studies.export(study_id)
        parsed_pgns = parser.import_user_lichess(pgns)
        await add_new_study(user.username, study_id, study_games=parsed_pgns)
        return {study_id: parsed_pgns}
    except:
        return HTTPException(403, "Provided key has not enough priviliges. Required priviliges: study:read")



@router.delete("/{study}")
async def remove_user_study(study: str, user: Annotated[User, Depends(get_current_active_user)]):
    is_removed = await  remove_study(user.username, study)
    if is_removed:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.delete("/{game_index}")
async def remove_user_game(game_index: int, user: Annotated[User, Depends(get_current_active_user)] ):
    is_removed = await remove_game(user.username, game_index)
    if is_removed:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.delete("/{study_name}/{game_index}")
async def remove_game_from_study(game_index: int, study_name: str,  user: Annotated[User, Depends(get_current_active_user)] ):
    is_removed = await remove_game(user.username, game_index, study_name)
    if is_removed:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.put("/update/game")
async def update_game_data(game_data: PGNGame, index: int, user: Annotated[User, Depends(get_current_active_user)], study: str | None = None ):
    is_updated = await update_game_moves(user, index, game_data, study)
    if is_updated:
        return Response(status_code=status.HTTP_200_OK, content=str(game_data.model_dump_json()))
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

@router.put("/updateToken")
async def update_token(token: str, user: Annotated[User, Depends(get_current_active_user)]):
    updated_succesfully = await update_lichess_token(user.username, token)
    if updated_succesfully:
        user.lichess_key = token
        return Response(status_code=200)
    return HTTPException(400, "Something bad happened during update")