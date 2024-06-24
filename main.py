from fastapi import FastAPI, Security, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader
import berserk
import uvicorn
import pgn_parser
from auth import router as auth_route
from pgn_routes import router as pgn_route

app = FastAPI(
    title="Chess api playground"
)
app.include_router(auth_route)
app.include_router(pgn_route)


@app.get("/isAlive")
async def liveness_endpoint():
    return {
        "message": "I am alive"
    }


@app.get(
        "/isReady"
)
async def readiness_endpoint():
    return {
        "message": "I am ready to work"
    }


@app.get("/")
async def redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run(app, port=8000)