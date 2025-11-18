from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from dotenv import load_dotenv
import os
import logging

# Import API routers
from .api.v1.intelligence import router as intelligence_router
from .api.v1.tags import router as tags_router
from .api.v1.verification import router as verification_router
from .api.v1.alerts import router as alerts_router
from .api.v1.incidents import router as incidents_router
from .api.v1.personnel import router as personnel_router
from .api.v1.search import router as search_router
from .api.v1.metrics import router as metrics_router
from .api.v1.collaboration import router as collaboration_router

# Import middleware
from .middleware.audit_logging import AuditLoggingMiddleware
from .middleware.rate_limiting import RateLimitMiddleware
from .services.metrics_service import MetricsMiddleware

# Import WebSocket manager
from .websocket.manager import ConnectionManager

# Import authentication
from .auth import Token, User, authenticate_user, create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="WATCHKEEPER API",
    description="Advanced Missionary Intelligence & Personnel Safety System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize WebSocket manager
ws_manager = ConnectionManager()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditLoggingMiddleware)

# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=Token, tags=["authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    logger.info(f"User {user.username} logged in successfully")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/v1/auth/me", response_model=User, tags=["authentication"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user

# Include all API routers
app.include_router(
    intelligence_router,
    prefix="/api/v1/intelligence",
    tags=["intelligence"]
)
app.include_router(
    alerts_router,
    prefix="/api/v1/alerts",
    tags=["alerts"]
)
app.include_router(
    incidents_router,
    prefix="/api/v1/incidents",
    tags=["incidents"]
)
app.include_router(
    personnel_router,
    prefix="/api/v1/personnel",
    tags=["personnel"]
)
app.include_router(
    search_router,
    prefix="/api/v1/search",
    tags=["search"]
)
app.include_router(
    collaboration_router,
    prefix="/api/v1/collaboration",
    tags=["collaboration"]
)
app.include_router(
    tags_router,
    prefix="/api/v1/tags",
    tags=["tags"]
)
app.include_router(
    verification_router,
    prefix="/api/v1/verification",
    tags=["verification"]
)
app.include_router(
    metrics_router,
    prefix="/api/v1",
    tags=["monitoring"]
)

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time updates

    Supports topics:
    - intelligence: New intelligence items
    - alerts: Alert updates
    - incidents: Incident updates
    - personnel_tracking: Personnel location updates
    - system_status: System health updates
    """
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()

            # Handle subscribe/unsubscribe requests
            if data.get("action") == "subscribe":
                topic = data.get("topic")
                if topic:
                    ws_manager.subscribe(user_id, topic)
                    await websocket.send_json({
                        "type": "subscription",
                        "status": "subscribed",
                        "topic": topic
                    })

            elif data.get("action") == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    ws_manager.unsubscribe(user_id, topic)
                    await websocket.send_json({
                        "type": "subscription",
                        "status": "unsubscribed",
                        "topic": topic
                    })

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")

# Dashboard endpoint
@app.get("/api/v1/dashboard/stats", tags=["dashboard"])
async def get_dashboard_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get dashboard statistics overview
    """
    from .database import SessionLocal
    from .models.intelligence import IntelligenceItem
    from .models.alert import Alert
    from .models.incident import FieldIncident
    from .models.personnel import Personnel
    from datetime import datetime, timedelta
    from sqlalchemy import func

    db = SessionLocal()
    try:
        # Get statistics
        total_intelligence = db.query(IntelligenceItem).count()

        active_alerts = db.query(Alert).filter(
            Alert.status == 'active'
        ).count()

        unacknowledged_alerts = db.query(Alert).filter(
            Alert.status == 'active',
            Alert.acknowledged_at == None
        ).count()

        open_incidents = db.query(FieldIncident).filter(
            FieldIncident.status.in_(['reported', 'investigating'])
        ).count()

        active_personnel = db.query(Personnel).filter(
            Personnel.status == 'active'
        ).count()

        # Personnel in danger zones (would need geofence check)
        personnel_in_danger = 0  # Placeholder

        # Average threat level
        avg_threat = db.query(func.avg(IntelligenceItem.threat_level)).scalar() or 0

        # Recent collections (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_collections = db.query(IntelligenceItem).filter(
            IntelligenceItem.created_at >= yesterday
        ).count()

        return {
            "total_intelligence": total_intelligence,
            "active_alerts": active_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "open_incidents": open_incidents,
            "active_personnel": active_personnel,
            "personnel_in_danger": personnel_in_danger,
            "threat_level_avg": float(avg_threat),
            "recent_collections": recent_collections
        }

    finally:
        db.close()

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    API root endpoint
    """
    return {
        "message": "Welcome to WATCHKEEPER API",
        "version": "2.0.0",
        "description": "Advanced Missionary Intelligence & Personnel Safety System",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# Health check endpoint
@app.get("/api/v1/health", tags=["monitoring"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    """
    return {
        "status": "healthy",
        "service": "watchkeeper-api",
        "version": "2.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Run on application startup
    """
    logger.info("🚀 WATCHKEEPER API v2.0 starting...")
    logger.info("📡 WebSocket manager initialized")
    logger.info("✅ All API routes registered")
    logger.info("🔒 Security middleware enabled")
    logger.info("📊 Metrics collection enabled")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown
    """
    logger.info("👋 WATCHKEEPER API shutting down...")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Mount static files for frontend (production)
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
