from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from .service import IdentityService
from .models import UserProfile, AuthenticationResult

# Pydantic models for API
class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str
    profile: Optional[UserProfile] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime

class APIKeyRequest(BaseModel):
    name: str
    expires_in_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    key: str
    name: str
    expires_at: Optional[datetime] = None

# Create FastAPI app
app = FastAPI(title="Identity Service API")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Service instance will be injected
identity_service: IdentityService = None

def init_api(service: IdentityService):
    """Initialize the API with service instance"""
    global identity_service
    identity_service = service

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency for getting current user from token"""
    claims = await identity_service.validate_token(token)
    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims["sub"]

@app.post("/register", response_model=TokenResponse)
async def register(registration: UserRegistration):
    """Register a new user"""
    result = await identity_service.register_user(
        registration.username,
        registration.email,
        registration.password,
        registration.profile
    )
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error_message
        )
        
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_at=result.expires_at
    )

@app.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    result = await identity_service.authenticate(
        form_data.username,
        form_data.password
    )
    
    if not result.success:
        raise HTTPException(
            status_code=401,
            detail=result.error_message,
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_at=result.expires_at
    )

@app.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Header(...)):
    """Refresh access token"""
    result = await identity_service.refresh_token(refresh_token)
    
    if not result.success:
        raise HTTPException(
            status_code=401,
            detail=result.error_message,
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=refresh_token,
        expires_at=result.expires_at
    )

@app.get("/profile", response_model=UserProfile)
async def get_profile(current_user: str = Depends(get_current_user)):
    """Get current user's profile"""
    profile = await identity_service.get_user_profile(current_user)
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
        
    return profile

@app.put("/profile", response_model=UserProfile)
async def update_profile(
    profile: UserProfile,
    current_user: str = Depends(get_current_user)
):
    """Update current user's profile"""
    success = await identity_service.update_user_profile(current_user, profile)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to update profile"
        )
        
    return profile

@app.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new API key"""
    key = await identity_service.create_api_key(
        current_user,
        request.name,
        request.expires_in_days
    )
    
    if not key:
        raise HTTPException(
            status_code=400,
            detail="Failed to create API key"
        )
        
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
    return APIKeyResponse(
        key=key,
        name=request.name,
        expires_at=expires_at
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = await identity_service.health_check()
    return {
        "status": status.status,
        "version": status.version,
        "uptime": status.uptime,
        "last_check": status.last_check
    } 