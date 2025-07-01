from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from dotenv import load_dotenv
import os

# Import API routers
from api.v1.intelligence import router as intelligence_router
from api.v1.tags import router as tags_router
from api.v1.verification import router as verification_router

# Import authentication
from .auth import Token, User, authenticate_user, create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES, users_db

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="WATCHKEEPER API",
    description="Intelligence monitoring system for missionary safety",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication endpoints
@app.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(users_db, form_data.username, form_data.password)
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
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User, tags=["auth"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Include API routers
app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
app.include_router(tags_router, prefix="/api/v1/tags", tags=["tags"])
app.include_router(verification_router, prefix="/api/v1/verification", tags=["verification"])

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to WATCHKEEPER API"}

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Mount static files if needed
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
