from fastapi import FastAPI
from api.routers import matches, matchups, players, rankings

app = FastAPI(
    title="Tennis Stats API",
    description="""
    A comprehensive tennis statistics and prediction API.
    
    This API provides access to historical match data, player performance metrics, 
    real-time Elo ratings, and head-to-head match predictions.
    """,
    version="1.0.0",
)
app.include_router(players.router)
app.include_router(matchups.router)
app.include_router(matches.router)
app.include_router(rankings.router)


@app.get("/")
async def root():
    return {"message": "Welcome to my tennis stats API!"}
