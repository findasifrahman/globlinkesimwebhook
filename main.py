from fastapi import FastAPI, Request
import logging
from databases import Database
from sqlalchemy import MetaData, Table, Column, String, DateTime, Numeric, create_engine
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Log DATABASE_URL with masked password for debugging
masked_url = DATABASE_URL.replace(DATABASE_URL.split('@')[0], '***')
logging.info(f"Connecting to database: {masked_url}")

database = Database(DATABASE_URL)
metadata = MetaData()

app = FastAPI()
logging.basicConfig(level=logging.INFO)
latest_events = []  # stores webhook events temporarily



########################################################


# 🚀 Define Table
payment_webhook_states = Table(
    "payment_webhook_states",
    metadata,
    Column("id", String, primary_key=True),
    Column("order_id", String),
    Column("status", String),
    Column("transaction_id", String),
    Column("pm_id", String),
    Column("amount", Numeric(10, 2)),
    Column("currency", String),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("user_id", String),
)

@app.on_event("startup")
async def startup():
    try:
        # Create table if it doesn't exist
        engine = create_engine(DATABASE_URL)
        metadata.create_all(engine)
        
        # Connect to database
        await database.connect()
        logging.info("Successfully connected to database")
    except Exception as e:
        logging.error(f"Failed to connect to database: {str(e)}")
        raise

@app.post("/globlinkesimwebhook")
async def hook(request: Request):
    payload = await request.json()
    latest_events.append(payload)
    logging.info(f"📩 Webhook: {payload}")
    return {"status": "ok"}

    
@app.get("/last-events")
def get_last_events():
    return {"events": latest_events[-10:]}  # return latest 10

########################################################

@app.post("/payssiongloblinkesimwebhhok")
async def hook(request: Request):
    payload = await request.json()
    logging.info(f"📩 Webhook: {payload}")

    order_id = payload.get("order_id")
    transaction_id = payload.get("transaction_id")
    state = payload.get("state")
    pm_id = payload.get("pm_id")
    amount = payload.get("amount")
    currency = payload.get("currency")

    if not order_id:
        return {"error": "order_id missing"}

    now = datetime.utcnow()

    # 🚀 Build UPSERT query
    upsert_query = insert(payment_webhook_states).values(
        id=transaction_id,
        order_id=order_id,
        status=state,
        transaction_id=transaction_id,
        pm_id=pm_id,
        amount=amount,
        currency=currency,
        created_at=now,
        updated_at=now,
        user_id=None,
    ).on_conflict_do_update(
        index_elements=['id'],
        set_={
            "status": state,
            "updated_at": now,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "pm_id": pm_id
        }
    )

    await database.execute(upsert_query)
    return {"status": "ok"}


# 🚀 Endpoint to view latest payment webhook events
@app.get("/last-events-payment-webhook")
async def get_last_events():
    query = payment_webhook_states.select().order_by(payment_webhook_states.c.created_at.desc()).limit(10)
    events = await database.fetch_all(query)
    return {"events": [dict(event) for event in events]}

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
