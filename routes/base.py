from dependencies import parser
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from .auth import get_current_active_user

router = APIRouter(
    tags=["base"],
    dependencies=[Depends(get_current_active_user)]
)




@router.post("/upload/PGN")
async def import_pgn_file(file: UploadFile):
    if file.content_type != "application/octet-stream":
        raise HTTPException(422, "Invalid input type")
    pgn = parser.import_user_pgn(await file.read())
    # TODO: Test it against real pgn file 
    return pgn