# keycloak_auth.py - Keycloak OIDC authentication integration for FinVault
# Simulates token validation, session management, and SSO login flows

import os
import json
import time
from typing import Dict, Any, Optional

# Mock Keycloak configuration
KEYCLOAK_CONFIG = {
    "realm": "finvault",
    "server_url": os.getenv("KEYCLOAK_SERVER_URL", "http://keycloak:8080"),
    "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "finvault-portal"),
    "client_secret": os.getenv("KEYCLOAK_CLIENT_SECRET", "finvault-secret-2026"),
    "token_endpoint": "/realms/finvault/protocol/openid-connect/token",
    "userinfo_endpoint": "/realms/finvault/protocol/openid-connect/userinfo",
    "session_ttl_seconds": 3600
}

# In-memory session store (Redis-backed in production)
SESSION_STORE: Dict[str, Dict[str, Any]] = {}

class KeycloakAuthService:
    """
    Handles Keycloak OIDC authentication flows:
    - Student login (student role)
    - Finance Officer login (officer role)
    - JWT token validation and refresh
    - Session management
    """

    @staticmethod
    def authenticate_user(username: str, password: str, role: str = "student") -> Dict[str, Any]:
        """
        Mock Keycloak authentication — in production, this POSTs to Keycloak token endpoint.
        Returns a signed session token and user details.
        """
        # Simulate credential check
        MOCK_USERS = {
            "arjun.shah": {"student_id": "STU-2021-4892", "name": "Arjun Shah", "role": "student", "currency": "INR"},
            "sarah.connor": {"student_id": "STU-2022-1082", "name": "Sarah Connor", "role": "student", "currency": "USD"},
            "sarah.jenkins": {"officer_id": "FO-SARAH-001", "name": "Sarah Jenkins", "role": "finance_officer"},
        }

        user = MOCK_USERS.get(username)
        if not user or user["role"] != role:
            return {"success": False, "error": "Invalid credentials or role mismatch."}

        session_token = f"kc-token-{username}-{int(time.time())}"
        SESSION_STORE[session_token] = {
            **user,
            "issued_at": time.time(),
            "expires_at": time.time() + KEYCLOAK_CONFIG["session_ttl_seconds"],
            "session_state": f"sess-{int(time.time())}"
        }

        print(f"[KEYCLOAK] User '{username}' authenticated with role '{role}'. Session: {session_token}")
        return {
            "success": True,
            "access_token": session_token,
            "token_type": "Bearer",
            "expires_in": KEYCLOAK_CONFIG["session_ttl_seconds"],
            "user": user
        }

    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """Validates a bearer token against the in-memory session store."""
        session = SESSION_STORE.get(token)
        if not session:
            return None
        if time.time() > session["expires_at"]:
            del SESSION_STORE[token]
            print(f"[KEYCLOAK] Session expired and removed: {token}")
            return None
        return session

    @staticmethod
    def logout(token: str) -> bool:
        """Revokes session token (Keycloak backchannel logout)."""
        if token in SESSION_STORE:
            del SESSION_STORE[token]
            print(f"[KEYCLOAK] Session revoked: {token}")
            return True
        return False

    @staticmethod
    def get_realm_info() -> Dict[str, Any]:
        return {
            "realm": KEYCLOAK_CONFIG["realm"],
            "server_url": KEYCLOAK_CONFIG["server_url"],
            "client_id": KEYCLOAK_CONFIG["client_id"],
            "sso_enabled": True,
            "mfa_required": True
        }
