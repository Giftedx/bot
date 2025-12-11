from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from shared.utils.service_interface import BaseService
from shared.security.security_service import SecurityService, TokenType
from infrastructure.database.database_service import DatabaseService
from infrastructure.cache.cache_service import CacheService
from infrastructure.storage.storage_service import StorageService
from infrastructure.database.models import User, Role, APIKey
from .models import UserProfile, AuthenticationResult, PermissionSet, RoleDefinition, SYSTEM_ROLES

class IdentityService(BaseService):
    """Service for managing user identity and authentication"""
    
    def __init__(self,
                 security_service: SecurityService,
                 database_service: DatabaseService,
                 cache_service: CacheService,
                 storage_service: Optional[StorageService] = None):
        super().__init__("identity", "1.0.0")
        self.security = security_service
        self.db = database_service
        self.cache = cache_service
        self.storage = storage_service
        self.logger = logging.getLogger(__name__)
        
        # Cache settings
        self.profile_cache_ttl = 3600  # 1 hour
        self.session_cache_ttl = 86400  # 24 hours
        
    async def _init_dependencies(self) -> None:
        """Initialize service dependencies"""
        # Ensure system roles exist
        await self._init_system_roles()
    
    async def _start_service(self) -> None:
        """Start the identity service"""
        self.logger.info("Identity service started")
    
    async def _stop_service(self) -> None:
        """Stop the identity service"""
        self.logger.info("Identity service stopped")
    
    async def _cleanup_resources(self) -> None:
        """Cleanup service resources"""
        pass
    
    async def _init_system_roles(self):
        """Initialize system roles in database"""
        for role_id, role_def in SYSTEM_ROLES.items():
            existing_role = self.db.get_all(Role, {"name": role_def.name})
            if not existing_role:
                role = Role(
                    name=role_def.name,
                    description=role_def.description,
                    permissions=role_def.permissions.__dict__
                )
                self.db.create(role)
                self.logger.info(f"Created system role: {role_def.name}")
    
    async def register_user(self,
                          username: str,
                          email: str,
                          password: str,
                          profile: Optional[UserProfile] = None) -> AuthenticationResult:
        """Register a new user"""
        try:
            # Check if user exists
            existing_user = self.db.get_all(User, {"username": username})
            if existing_user:
                return AuthenticationResult(
                    success=False,
                    error_message="Username already exists"
                )
                
            # Validate password strength
            if not self.security.validate_password_strength(password):
                return AuthenticationResult(
                    success=False,
                    error_message="Password does not meet security requirements"
                )
                
            # Create user
            password_hash = self.security.hash_password(password)
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                is_active=True
            )
            
            # Add default user role
            default_role = self.db.get_all(Role, {"name": SYSTEM_ROLES["user"].name})[0]
            user.roles.append(default_role)
            
            # Save user
            user = self.db.create(user)
            
            # Generate tokens
            access_token = self.security.generate_token(
                str(user.id),
                TokenType.ACCESS
            )
            refresh_token = self.security.generate_token(
                str(user.id),
                TokenType.REFRESH
            )
            
            # Cache tokens
            self.cache.store_token(access_token.token, str(user.id))
            self.cache.store_token(refresh_token.token, str(user.id))
            
            return AuthenticationResult(
                success=True,
                user_id=str(user.id),
                access_token=access_token.token,
                refresh_token=refresh_token.token,
                expires_at=access_token.expires_at
            )
            
        except Exception as e:
            self.logger.error(f"Error registering user: {e}")
            return AuthenticationResult(
                success=False,
                error_message="Registration failed"
            )
    
    async def authenticate(self, username: str, password: str) -> AuthenticationResult:
        """Authenticate a user"""
        try:
            # Get user
            users = self.db.get_all(User, {"username": username})
            if not users:
                self.security.record_failed_attempt(username)
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            user = users[0]
            
            # Check if account is locked
            if self.security.is_account_locked(str(user.id)):
                return AuthenticationResult(
                    success=False,
                    error_message="Account is locked"
                )
            
            # Verify password
            if not self.security.verify_password(password, user.password_hash):
                self.security.record_failed_attempt(str(user.id))
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            # Clear failed attempts
            self.security.clear_failed_attempts(str(user.id))
            
            # Generate tokens
            access_token = self.security.generate_token(
                str(user.id),
                TokenType.ACCESS,
                {"roles": [r.name for r in user.roles]}
            )
            refresh_token = self.security.generate_token(
                str(user.id),
                TokenType.REFRESH
            )
            
            # Cache tokens
            self.cache.store_token(access_token.token, str(user.id))
            self.cache.store_token(refresh_token.token, str(user.id))
            
            # Update last login
            self.db.update(user, {"last_login": datetime.utcnow()})
            
            return AuthenticationResult(
                success=True,
                user_id=str(user.id),
                access_token=access_token.token,
                refresh_token=refresh_token.token,
                expires_at=access_token.expires_at
            )
            
        except Exception as e:
            self.logger.error(f"Error authenticating user: {e}")
            return AuthenticationResult(
                success=False,
                error_message="Authentication failed"
            )
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an access token"""
        # Check cache first
        user_id = self.cache.get_token_user(token)
        if not user_id:
            # Verify token
            claims = self.security.verify_token(token)
            if claims and claims["type"] == TokenType.ACCESS.value:
                # Cache valid token
                self.cache.store_token(token, claims["sub"])
                return claims
            return None
        return {"sub": user_id, "type": TokenType.ACCESS.value}
    
    async def refresh_token(self, refresh_token: str) -> AuthenticationResult:
        """Refresh an access token"""
        try:
            # Verify refresh token
            claims = self.security.verify_token(refresh_token)
            if not claims or claims["type"] != TokenType.REFRESH.value:
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid refresh token"
                )
            
            user_id = claims["sub"]
            user = self.db.get_by_id(User, int(user_id))
            if not user:
                return AuthenticationResult(
                    success=False,
                    error_message="User not found"
                )
            
            # Generate new access token
            access_token = self.security.generate_token(
                user_id,
                TokenType.ACCESS,
                {"roles": [r.name for r in user.roles]}
            )
            
            # Cache new token
            self.cache.store_token(access_token.token, user_id)
            
            return AuthenticationResult(
                success=True,
                user_id=user_id,
                access_token=access_token.token,
                expires_at=access_token.expires_at
            )
            
        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            return AuthenticationResult(
                success=False,
                error_message="Token refresh failed"
            )
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get a user's profile"""
        # Check cache first
        cache_key = f"profile:{user_id}"
        profile = self.cache.get(cache_key)
        if profile:
            return UserProfile(**profile)
            
        # Get from database
        user = self.db.get_by_id(User, int(user_id))
        if not user:
            return None
            
        # Create profile
        profile = UserProfile(
            display_name=user.username,
            avatar_url=user.avatar_url,
            bio=None,
            social_links={},
            preferences={}
        )
        
        # Cache profile
        self.cache.set(cache_key, profile.__dict__, self.profile_cache_ttl)
        
        return profile
    
    async def update_user_profile(self, user_id: str, profile: UserProfile) -> bool:
        """Update a user's profile"""
        try:
            user = self.db.get_by_id(User, int(user_id))
            if not user:
                return False

            # Update user fields if needed (e.g. avatar_url is stored in User model)
            if profile.avatar_url:
                self.db.update(user, {"avatar_url": profile.avatar_url})
                
            # Update cache
            cache_key = f"profile:{user_id}"
            self.cache.set(cache_key, profile.__dict__, self.profile_cache_ttl)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating profile: {e}")
            return False

    async def upload_avatar(self, user_id: str, file_data: bytes, filename: str) -> Optional[str]:
        """Upload a user avatar"""
        if not self.storage:
            self.logger.error("Storage service not initialized")
            return None

        try:
            user = self.db.get_by_id(User, int(user_id))
            if not user:
                return None

            # Save file using storage service
            # Store in 'avatars' subfolder
            relative_path = self.storage.save_file(file_data, filename, "avatars")

            if relative_path:
                # Update user profile with new avatar URL/path
                self.db.update(user, {"avatar_url": relative_path})

                # Invalidate cache
                cache_key = f"profile:{user_id}"
                self.cache.delete(cache_key)

                return relative_path

            return None

        except Exception as e:
            self.logger.error(f"Error uploading avatar: {e}")
            return None
    
    async def get_user_permissions(self, user_id: str) -> PermissionSet:
        """Get combined permissions for a user"""
        user = self.db.get_by_id(User, int(user_id))
        if not user:
            return PermissionSet()
            
        # Combine permissions from all roles
        combined = PermissionSet()
        for role in user.roles:
            role_perms = role.permissions
            for perm, value in role_perms.items():
                if value:
                    setattr(combined, perm, True)
                    
        return combined
    
    async def create_api_key(self, user_id: str, name: str, 
                            expires_in_days: Optional[int] = None) -> Optional[str]:
        """Create an API key for a user"""
        try:
            user = self.db.get_by_id(User, int(user_id))
            if not user:
                return None
                
            key = self.security.generate_api_key()
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
                
            api_key = APIKey(
                user_id=user.id,
                key=key,
                name=name,
                expires_at=expires_at,
                is_active=True
            )
            
            self.db.create(api_key)
            return key
            
        except Exception as e:
            self.logger.error(f"Error creating API key: {e}")
            return None
    
    async def validate_api_key(self, key: str) -> Optional[str]:
        """Validate an API key and return user ID if valid"""
        try:
            keys = self.db.get_all(APIKey, {"key": key, "is_active": True})
            if not keys:
                return None
                
            api_key = keys[0]
            
            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return None
                
            # Update last used
            self.db.update(api_key, {"last_used": datetime.utcnow()})
            
            return str(api_key.user_id)
            
        except Exception as e:
            self.logger.error(f"Error validating API key: {e}")
            return None 