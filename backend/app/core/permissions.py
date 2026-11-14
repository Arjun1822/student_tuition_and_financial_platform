import enum
from typing import List, Union
from fastapi import HTTPException, status, Depends


class UserRole(str, enum.Enum):
    LEARNER = "LEARNER"
    INSTRUCTOR = "INSTRUCTOR"
    ACADEMIC_ADMIN = "ACADEMIC_ADMIN"
    SUPPORT_STAFF = "SUPPORT_STAFF"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


def require_role(allowed_role: Union[UserRole, str]):
    """Dependency factory checking that the current user has the required role."""
    from app.api.dependencies import get_current_user
    
    role_str = allowed_role.value if isinstance(allowed_role, UserRole) else allowed_role

    def role_checker(current_user=Depends(get_current_user)):
        user_role = getattr(current_user, "role", None)
        user_role_str = user_role.value if hasattr(user_role, "value") else str(user_role)
        
        # PLATFORM_ADMIN has superset privileges
        if user_role_str == UserRole.PLATFORM_ADMIN.value:
            return current_user
            
        if user_role_str != role_str:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {role_str}"
            )
        return current_user

    return role_checker


def require_any_role(allowed_roles: List[Union[UserRole, str]]):
    """Dependency factory allowing any of the specified roles."""
    from app.api.dependencies import get_current_user
    
    allowed_set = {
        r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles
    }
    # Platform admin is always allowed
    allowed_set.add(UserRole.PLATFORM_ADMIN.value)

    def role_checker(current_user=Depends(get_current_user)):
        user_role = getattr(current_user, "role", None)
        user_role_str = user_role.value if hasattr(user_role, "value") else str(user_role)
        
        if user_role_str not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required one of roles: {list(allowed_set)}"
            )
        return current_user

    return role_checker
