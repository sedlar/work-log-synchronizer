"""OAuth 2.0 authentication for BambooHR API."""

import json
import logging
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs

import httpx

from work_log_sync.utils import StorageManager

logger = logging.getLogger(__name__)


class BambooHROAuthConfig:
    """Configuration for BambooHR OAuth."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        domain: str,
        redirect_uri: str = "http://localhost:8000/callback",
    ) -> None:
        """Initialize OAuth configuration.

        Args:
            client_id: OAuth client ID.
            client_secret: OAuth client secret.
            domain: BambooHR domain (e.g., 'mycompany').
            redirect_uri: OAuth redirect URI.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain
        self.redirect_uri = redirect_uri
        self.base_url = f"https://{domain}.bamboohr.com"


class OAuthToken:
    """OAuth token data model."""

    def __init__(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int = 3600,
    ) -> None:
        """Initialize OAuth token.

        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token (optional).
            expires_in: Token expiration time in seconds.
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OAuthToken":
        """Create from dictionary stored in storage."""
        token = cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=0,
        )
        token.expires_at = datetime.fromisoformat(data["expires_at"])
        return token


class AuthorizationCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    authorization_code: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        """Handle GET request from OAuth redirect."""
        parsed_path = urlparse(self.path)
        if parsed_path.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        query_params = parse_qs(parsed_path.query)

        if "error" in query_params:
            AuthorizationCallbackHandler.error = query_params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authorization Error</h1>"
                b"<p>The authorization failed. You can close this window.</p>"
                b"</body></html>"
            )
            return

        if "code" in query_params:
            AuthorizationCallbackHandler.authorization_code = query_params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authorization Successful</h1>"
                b"<p>You have successfully authorized the application. "
                b"You can close this window.</p>"
                b"</body></html>"
            )
            return

        self.send_response(400)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress log messages."""
        pass


class BambooHROAuthClient:
    """Client for handling BambooHR OAuth 2.0 flow."""

    SCOPES = [
        "email", "openid",
        "time_tracking:read",
        "offline_access",
    ]

    def __init__(
        self,
        config: BambooHROAuthConfig,
        storage: StorageManager | None = None,
    ) -> None:
        """Initialize BambooHR OAuth client.

        Args:
            config: OAuth configuration.
            storage: StorageManager instance for token caching.
        """
        self.config = config
        self.storage = storage or StorageManager()
        self._token: OAuthToken | None = None

    def get_authorization_url(self, state: str = "state") -> str:
        """Generate authorization URL for user to visit.

        Args:
            state: CSRF protection state parameter.

        Returns:
            Authorization URL.
        """
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": "+".join(self.SCOPES),
            "state": state,
        }
        return f"{self.config.base_url}/authorize.php?request=authorize&{urlencode(params)}"

    def handle_callback(self) -> OAuthToken:
        """Start local server to handle OAuth callback and obtain token.

        Returns:
            OAuthToken with access and refresh tokens.

        Raises:
            RuntimeError: If authorization fails or times out.
        """
        # Parse redirect URI to get host and port
        parsed_uri = urlparse(self.config.redirect_uri)
        host = parsed_uri.hostname or "localhost"
        port = parsed_uri.port or 8000

        # Reset class variables
        AuthorizationCallbackHandler.authorization_code = None
        AuthorizationCallbackHandler.error = None

        # Create and start local server
        server = HTTPServer((host, port), AuthorizationCallbackHandler)
        server_thread = Thread(target=server.handle_request)
        server_thread.daemon = True
        server_thread.start()

        # Open authorization URL in browser
        auth_url = self.get_authorization_url()
        logger.info(f"Opening browser for authorization: {auth_url}")
        webbrowser.open(auth_url)

        # Wait for callback (with timeout)
        logger.info("Waiting for authorization callback...")
        server_thread.join(timeout=300)  # 5 minute timeout
        server.server_close()

        if AuthorizationCallbackHandler.error:
            raise RuntimeError(
                f"Authorization failed: {AuthorizationCallbackHandler.error}"
            )

        if not AuthorizationCallbackHandler.authorization_code:
            raise RuntimeError(
                "Authorization timeout or no authorization code received"
            )

        # Exchange code for token
        code = AuthorizationCallbackHandler.authorization_code
        token = self._exchange_code_for_token(code)
        self._token = token

        # Store token
        self.storage.set_token(
            "bamboohr_oauth",
            json.dumps(token.to_dict()),
        )

        return token

    def _exchange_code_for_token(self, code: str) -> OAuthToken:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from callback.

        Returns:
            OAuthToken.

        Raises:
            httpx.HTTPError: If token exchange fails.
        """
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": self.config.redirect_uri,
        }

        response = httpx.post(f"{self.config.base_url}/token.php", data=payload)
        response.raise_for_status()

        data = response.json()
        token = OAuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in", 3600),
        )

        logger.info("Successfully obtained OAuth token")
        return token

    def get_token(self) -> OAuthToken:
        """Get current token, refreshing if necessary.

        Returns:
            OAuthToken.

        Raises:
            RuntimeError: If token is not available or refresh fails.
        """
        if self._token is None:
            # Try to load from storage
            stored_token = self.storage.get_token("bamboohr_oauth")
            if stored_token:
                try:
                    token_data = json.loads(stored_token)
                    self._token = OAuthToken.from_dict(token_data)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to load stored token: {e}")

        if self._token is None:
            raise RuntimeError(
                "No token available. Please run authentication first."
            )

        # Refresh if expired
        if self._token.is_expired():
            if self._token.refresh_token:
                logger.info("Token expired, refreshing...")
                self._token = self.refresh_token()
            else:
                raise RuntimeError(
                    "Token expired and no refresh token available. "
                    "Please re-authenticate."
                )

        return self._token

    def refresh_token(self) -> OAuthToken:
        """Refresh access token using refresh token.

        Returns:
            New OAuthToken.

        Raises:
            RuntimeError: If refresh token is not available.
            httpx.HTTPError: If token refresh fails.
        """
        if self._token is None or not self._token.refresh_token:
            raise RuntimeError("No refresh token available")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        response = httpx.post(f"{self.config.base_url}/token.php", data=payload)
        response.raise_for_status()

        data = response.json()
        token = OAuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", self._token.refresh_token),
            expires_in=data.get("expires_in", 3600),
        )

        self._token = token

        # Update stored token
        self.storage.set_token(
            "bamboohr_oauth",
            json.dumps(token.to_dict()),
        )

        logger.info("Token successfully refreshed")
        return token

    def clear_token(self) -> None:
        """Clear stored token."""
        self._token = None
        self.storage.delete_token("bamboohr_oauth")
