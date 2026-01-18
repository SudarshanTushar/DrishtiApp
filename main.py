from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import routing, voice
from sentinel import risk_engine
from command import dashboard

# --- SYSTEM INITIALIZATION ---
app = FastAPI(
    title="RouteAI-NE: Sentinel V2",
    description="Government-Grade Disaster Intelligence Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- SECURITY & CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BRAIN CONNECTION ---
app.include_router(routing.router)
app.include_router(voice.router)
app.include_router(risk_engine.router)
app.include_router(dashboard.router)

@app.get("/")
def system_health_check():
    """Heartbeat for Load Balancers"""
    return {
        "system": "RouteAI-NE",
        "status": "OPERATIONAL",
        "version": "2.0.0 (Sentinel)",
        "brains": {
            "core": "ONLINE",
            "sentinel": "ONLINE",
            "command": "ONLINE"
        }
    }
