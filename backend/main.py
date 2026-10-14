from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import data, prediction, inventory, consumption, waste, analytics, simulator, recommendations, operations
from services.storage import initialize_history_database

initialize_history_database()

app = FastAPI(title="FOODWISE AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://foodwise-ai-frontend.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api")
app.include_router(prediction.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(consumption.router, prefix="/api")
app.include_router(waste.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(simulator.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(operations.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "FOODWISE AI API is running"}

@app.get("/api/health")
def health():
    return {"status": "ok"}
