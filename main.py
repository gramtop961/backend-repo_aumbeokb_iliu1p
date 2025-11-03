import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Healer, Booking

app = FastAPI(title="Reiki Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Reiki Booking Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# Healers Endpoints
@app.post("/healers")
def create_healer(healer: Healer):
    try:
        inserted_id = create_document("healer", healer)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healers")
def list_healers(limit: Optional[int] = 100):
    try:
        docs = get_documents("healer", {}, limit)
        # Convert ObjectIds to strings
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bookings Endpoints
@app.post("/bookings")
def create_booking(booking: Booking):
    # Validate healer exists
    healer_oid = None
    try:
        healer_oid = ObjectId(booking.healer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid healer_id")

    healer = db["healer"].find_one({"_id": healer_oid}) if db is not None else None
    if not healer:
        raise HTTPException(status_code=404, detail="Healer not found")

    try:
        inserted_id = create_document("booking", booking)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookings")
def list_bookings(limit: Optional[int] = 100):
    try:
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": limit if isinstance(limit, int) else 100},
            {"$lookup": {
                "from": "healer",
                "localField": "healer_id",
                "foreignField": "_id",
                "as": "healer_info"
            }}
        ]
        # Ensure healer_id is ObjectId in aggregation context is tricky since healer_id stored as str
        # We'll fetch and enrich in Python for simplicity
        docs = get_documents("booking", {}, limit)
        result = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            # Attach healer minimal info
            try:
                h = db["healer"].find_one({"_id": ObjectId(d["healer_id"])})
                if h:
                    d["healer"] = {
                        "id": str(h.get("_id")),
                        "name": h.get("name"),
                        "specialty": h.get("specialty"),
                        "avatar_url": h.get("avatar_url")
                    }
            except Exception:
                pass
            result.append(d)
        # Sort by created_at desc
        result.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
