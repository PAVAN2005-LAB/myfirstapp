from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
import os

app = FastAPI()

# ✅ Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load telemetry data once (efficient for serverless)
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    TELEMETRY = json.load(f)

# ✅ GET route (browser-friendly)
@app.get("/")
def root():
    return {
        "message": "✅ FastAPI serverless endpoint is live on Vercel!",
        "usage": "Send a POST request with JSON body {\"regions\": [...], \"threshold_ms\": N}."
    }

# ✅ POST route (main logic)
@app.post("/")
async def region_metrics(request: Request):
    """
    Accepts: {"regions": ["emea", "apac"], "threshold_ms": 180}
    Returns: per-region metrics (avg_latency, p95_latency, avg_uptime, breaches)
    """
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

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for l in latencies if l > threshold)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return results
