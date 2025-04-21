from fastapi import FastAPI, Request
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
latest_events = []  # stores webhook events temporarily

@app.post("/globlinkesimwebhook")
async def hook(request: Request):
    payload = await request.json()
    latest_events.append(payload)
    logging.info(f"📩 Webhook: {payload}")
    return {"status": "ok"}

    
@app.get("/last-events")
def get_last_events():
    return {"events": latest_events[-10:]}  # return latest 10
