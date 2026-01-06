"""
PetInsure360 - Backend API
FastAPI application with WebSocket support for real-time updates
Writes data to Azure Data Lake Storage Gen2
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from contextlib import asynccontextmanager

from app.api import customers, pets, policies, claims, insights, recommendations, pipeline, scenarios, docgen
from app.services.storage import StorageService
from app.services.insights import InsightsService

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

# Initialize services
storage_service = StorageService()
insights_service = InsightsService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("PetInsure360 API Starting...")
    print(f"Storage configured: {storage_service.account_name}")

    # Load persisted demo data from Azure Storage
    try:
        loaded = await insights_service.load_persisted_demo_data(storage_service)
        if any(loaded.values()):
            print(f"Restored demo data: {loaded['customers']} customers, {loaded['pets']} pets, {loaded['claims']} claims")
    except Exception as e:
        print(f"Note: Could not load persisted demo data: {e}")

    # Auto-seed demo users on startup (DEMO-001, DEMO-002, DEMO-003)
    try:
        from app.api.customers import DEMO_USERS, DEMO_PETS, DEMO_POLICIES
        seeded = {"customers": 0, "pets": 0, "policies": 0}

        for user in DEMO_USERS:
            existing = insights_service.get_customer_360(customer_id=user["customer_id"])
            if not existing:
                insights_service.add_customer(user)
                seeded["customers"] += 1

        for pet in DEMO_PETS:
            pets = insights_service.get_customer_pets(pet["customer_id"])
            if not any(p.get("pet_id") == pet["pet_id"] for p in pets):
                insights_service.add_pet(pet)
                seeded["pets"] += 1

        for policy in DEMO_POLICIES:
            policies = insights_service.get_customer_policies(policy["customer_id"])
            if not any(p.get("policy_id") == policy["policy_id"] for p in policies):
                insights_service.add_policy(policy)
                seeded["policies"] += 1

        if any(seeded.values()):
            print(f"Auto-seeded demo users: {seeded['customers']} customers, {seeded['pets']} pets, {seeded['policies']} policies")
        else:
            print("Demo users already exist")
    except Exception as e:
        print(f"Note: Could not auto-seed demo users: {e}")

    yield
    # Shutdown
    print("PetInsure360 API Shutting down...")

# FastAPI app
app = FastAPI(
    title="PetInsure360 API",
    description="Pet Insurance Data Platform - Data Ingestion & BI Insights API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Include routers
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(pets.router, prefix="/api/pets", tags=["Pets"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(claims.router, prefix="/api/claims", tags=["Claims"])
app.include_router(insights.router, prefix="/api/insights", tags=["BI Insights"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Pet Recommendations"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Data Pipeline"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Claim Scenarios"])
app.include_router(docgen.router, prefix="/api/docgen", tags=["DocGen - AI Document Processing"])

# Make services available to routes
app.state.storage = storage_service
app.state.sio = sio
app.state.insights = insights_service

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PetInsure360 API",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "storage": {
            "account": storage_service.account_name,
            "container": storage_service.container_name
        },
        "websocket": "enabled"
    }

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Client connected to WebSocket."""
    print(f"Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to PetInsure360 real-time updates'}, to=sid)

@sio.event
async def disconnect(sid):
    """Client disconnected from WebSocket."""
    print(f"Client disconnected: {sid}")

@sio.event
async def subscribe_claims(sid, data):
    """Subscribe to claim status updates."""
    customer_id = data.get('customer_id')
    if customer_id:
        await sio.enter_room(sid, f"customer_{customer_id}")
        await sio.emit('subscribed', {'room': f"customer_{customer_id}"}, to=sid)

# Export socket app for uvicorn
def get_application():
    """Return the ASGI application with Socket.IO."""
    return socket_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:socket_app", host="0.0.0.0", port=3002, reload=True)
