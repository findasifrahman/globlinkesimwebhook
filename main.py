from fastapi import FastAPI, Request
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

@app.post("/globlinkesimwebhook")
async def hook(request: Request):
    payload = await request.json()
    logging.info(f"Got webhook: {payload}")
    return {"status": "ok"}

@app.get("/")
def root():
    return {"hello": "world"}
