from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
import os

app = FastAPI()

# ✅ Enable CORS for all origins (frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load telemetry data (available for all invocations)
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    TELEMETRY = json.load(f)

# ✅ Handle preflight (OPTIONS) requests
@app.options("/")
async def options_root():
    return {"allow": "POST"}

# ✅ Simple GET route for browser check
@app.get("/")
def root():
    return {
        "message": "✅ FastAPI serverless endpoint is live on Vercel!",
        "usage": "Send POST / with JSON {\"regions\": [...], \"threshold_ms\": N}"
    }

# ✅ POST route for telemetry metrics
@app.post("/")
async def region_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    results = {}
    for region in regions:
        region_records = [r for r in TELEMETRY if r["region"] == region]
        if not region_records:
            continue

        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_pct"] for r in region_records]

        results[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": sum(1 for l in latencies if l > threshold)
        }

    return results
