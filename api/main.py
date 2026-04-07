from fastapi import FastAPI
from routers import matches, players

app = FastAPI()
app.include_router(players.router)
app.include_router(matches.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
