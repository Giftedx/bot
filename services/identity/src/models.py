from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserProfile:
    """Extended user profile information"""
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    social_links: Dict[str, str] = None
    preferences: Dict[str, Any] = None

@dataclass
class AuthenticationResult:
    """Result of an authentication attempt"""
    success: bool
    user_id: Optional[str] = None
    error_message: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

@dataclass
class PermissionSet:
    """Set of permissions for a role"""
    can_read: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_manage_users: bool = False
    can_manage_roles: bool = False
    can_view_audit_logs: bool = False
    can_manage_system: bool = False

@dataclass
class RoleDefinition:
    """Role definition with permissions"""
    name: str
    description: str
    permissions: PermissionSet
    priority: int = 0
    is_system_role: bool = False

# Predefined system roles
SYSTEM_ROLES = {
    "admin": RoleDefinition(
        name="Administrator",
        description="Full system access",
        permissions=PermissionSet(
            can_read=True,
            can_write=True,
            can_delete=True,
            can_manage_users=True,
            can_manage_roles=True,
            can_view_audit_logs=True,
            can_manage_system=True
        ),
        priority=100,
        is_system_role=True
    ),
    "moderator": RoleDefinition(
        name="Moderator",
        description="User and content management",
        permissions=PermissionSet(
            can_read=True,
            can_write=True,
            can_delete=True,
            can_manage_users=True,
            can_view_audit_logs=True
        ),
        priority=50,
        is_system_role=True
    ),
    "user": RoleDefinition(
        name="User",
        description="Standard user access",
        permissions=PermissionSet(
            can_read=True,
            can_write=True
        ),
        priority=0,
        is_system_role=True
    )
} 