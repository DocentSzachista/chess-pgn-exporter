import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from routes.auth import router as auth_route
from routes.lichess import router as pgn_route
from routes.base import router as base_route
from database_models import client
from pymongo.errors import ConnectionFailure
from dependencies import LOGGER

app = FastAPI(
    title="Chess api playground"
)
app.include_router(auth_route)
app.include_router(pgn_route)
app.include_router(base_route)


@app.get("/isAlive")
async def liveness_endpoint():
    LOGGER.info("Check if API is alive")
    return {
        "message": "I am alive"
    }


@app.get(
        "/isReady"
)
async def readiness_endpoint():
    try:
        LOGGER.info("Check if database is set up")
        info = await client.admin.command("ping")
        return info
    except ConnectionFailure:
        LOGGER.error("Cant connect to the database")
        raise HTTPException(status_code=503, detail="Cant connect to the database")


@app.get("/")
async def redirect():
    LOGGER.info("Redirecting to docs")
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    LOGGER.info("Starting app.")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")