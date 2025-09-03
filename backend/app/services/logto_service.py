"""Logto Cloud integration service."""

from typing import Dict, Any, Optional
from logto import LogtoClient, LogtoConfig
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LogtoService:
    """Service for integrating with Logto Cloud."""
    
    def __init__(self):
        """Initialize Logto client."""
        self.client = LogtoClient(
            LogtoConfig(
                endpoint=settings.LOGTO_ENDPOINT,
                appId=settings.LOGTO_APP_ID,
                appSecret=str(settings.LOGTO_APP_SECRET),
            )
        )
    
    async def get_sign_in_url(self, redirect_uri: str) -> str:
        """Get Logto sign-in URL."""
        try:
            sign_in_url = await self.client.signIn(redirectUri=redirect_uri)
            return sign_in_url
        except Exception as e:
            logger.error(f"Failed to get sign-in URL: {e}")
            raise
    
    async def get_sign_out_url(self, post_logout_redirect_uri: str) -> str:
        """Get Logto sign-out URL."""
        try:
            sign_out_url = await self.client.signOut(
                postLogoutRedirectUri=post_logout_redirect_uri
            )
            return sign_out_url
        except Exception as e:
            logger.error(f"Failed to get sign-out URL: {e}")
            raise
    
    async def handle_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OIDC callback and exchange code for tokens."""
        try:
            # Exchange authorization code for tokens
            tokens = await self.client.handleSignInCallback(
                callbackUri=f"{redirect_uri}?code={code}"
            )
            
            # Get user info
            user_info = await self.client.fetchUserInfo()
            
            return {
                "access_token": tokens.access_token,
                "id_token": tokens.id_token,
                "user_info": user_info,
                "expires_in": tokens.expires_in
            }
        except Exception as e:
            logger.error(f"Failed to handle callback: {e}")
            raise
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        try:
            return self.client.isAuthenticated()
        except Exception as e:
            logger.error(f"Failed to check authentication status: {e}")
            return False
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information."""
        try:
            if self.is_authenticated():
                return await self.client.fetchUserInfo()
            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None


# Global Logto service instance
logto_service = LogtoService()
