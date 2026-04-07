from fastapi import FastAPI
from routers import matches, matchups, players, rankings

app = FastAPI()
app.include_router(players.router)
app.include_router(matchups.router)
app.include_router(matches.router)
app.include_router(rankings.router)


@app.get("/")
async def root():
    return {"message": "Welcome to my tennis stats API!"}
