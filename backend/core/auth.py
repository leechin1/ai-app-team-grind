"""
Supabase authentication middleware
"""
import os
from typing import Optional
from fastapi import Header, HTTPException
from supabase import create_client, Client


class AuthService:
    """Handle Supabase authentication"""

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials")

        self.client: Client = create_client(supabase_url, supabase_key)

    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return user data"""
        try:
            user = self.client.auth.get_user(token)

            if not user or not user.user:
                raise HTTPException(status_code=401, detail="Invalid token")

            return {
                "id": user.user.id,
                "email": user.user.email,
                "metadata": user.user.user_metadata
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# Global auth service
auth_service = AuthService()


# FastAPI dependency for protected routes
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Get current authenticated user.

    For development/testing: Returns a mock user if no auth header provided.
    For production: Require valid JWT token.
    """
    # DEVELOPMENT MODE: Allow access without auth for testing
    if not authorization:
        # Return mock user for testing (matches existing user in database)
        return {
            "id": "0495dca6-fd8a-471a-9a82-0ed3eb2b3b83",
            "email": "test@notiq.app",
            "metadata": {}
        }

    # Extract token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )

    token = parts[1]
    return auth_service.verify_token(token)


# Optional auth
async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Optional authentication"""
    if not authorization:
        return None

    try:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return auth_service.verify_token(parts[1])
    except:
        pass

    return None
