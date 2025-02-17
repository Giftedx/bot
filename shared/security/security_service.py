import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import secrets
from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    DISCORD = "discord"
    API = "api"

@dataclass
class UserToken:
    token: str
    token_type: TokenType
    expires_at: datetime
    user_id: str

class SecurityService:
    """Central security service for authentication and authorization"""
    
    def __init__(self, 
                 secret_key: str,
                 token_expiry: Dict[TokenType, int] = None,
                 max_failed_attempts: int = 5,
                 lockout_duration: int = 30):
        self.secret_key = secret_key
        self.token_expiry = token_expiry or {
            TokenType.ACCESS: 60,  # 1 hour
            TokenType.REFRESH: 60 * 24 * 7,  # 1 week
            TokenType.DISCORD: 60 * 24,  # 1 day
            TokenType.API: 60 * 24 * 30,  # 30 days
        }
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = lockout_duration
        self._failed_attempts: Dict[str, List[datetime]] = {}
        self._locked_accounts: Dict[str, datetime] = {}
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    def generate_token(self, user_id: str, token_type: TokenType, 
                      additional_claims: Optional[Dict] = None) -> UserToken:
        """Generate a JWT token"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.token_expiry[token_type])
        
        claims = {
            "sub": user_id,
            "type": token_type.value,
            "iat": now,
            "exp": expires_at
        }
        
        if additional_claims:
            claims.update(additional_claims)
            
        token = jwt.encode(claims, self.secret_key, algorithm="HS256")
        
        return UserToken(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            user_id=user_id
        )
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None
    
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    def record_failed_attempt(self, user_id: str):
        """Record a failed login attempt"""
        now = datetime.utcnow()
        if user_id not in self._failed_attempts:
            self._failed_attempts[user_id] = []
            
        # Remove attempts older than lockout duration
        self._failed_attempts[user_id] = [
            attempt for attempt in self._failed_attempts[user_id]
            if (now - attempt).total_seconds() < (self.lockout_duration * 60)
        ]
        
        self._failed_attempts[user_id].append(now)
        
        if len(self._failed_attempts[user_id]) >= self.max_failed_attempts:
            self._locked_accounts[user_id] = now
    
    def is_account_locked(self, user_id: str) -> bool:
        """Check if an account is locked due to too many failed attempts"""
        if user_id not in self._locked_accounts:
            return False
            
        lock_time = self._locked_accounts[user_id]
        now = datetime.utcnow()
        
        if (now - lock_time).total_seconds() >= (self.lockout_duration * 60):
            # Lock duration expired, remove lock
            del self._locked_accounts[user_id]
            if user_id in self._failed_attempts:
                del self._failed_attempts[user_id]
            return False
            
        return True
    
    def clear_failed_attempts(self, user_id: str):
        """Clear failed login attempts for a user"""
        if user_id in self._failed_attempts:
            del self._failed_attempts[user_id]
        if user_id in self._locked_accounts:
            del self._locked_accounts[user_id]
    
    def validate_password_strength(self, password: str) -> bool:
        """Validate password meets minimum security requirements"""
        if len(password) < 8:
            return False
            
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        return has_upper and has_lower and has_digit and has_special 