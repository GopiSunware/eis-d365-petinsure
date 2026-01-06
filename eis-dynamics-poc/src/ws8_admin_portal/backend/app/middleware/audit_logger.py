"""Audit logging middleware."""

import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests for audit purposes.
    Detailed audit logging is done in individual endpoints.
    """

    # Paths to exclude from logging
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Get user info if available
        user_id = "anonymous"
        user_name = "Anonymous"

        if hasattr(request.state, "user"):
            user = request.state.user
            user_id = getattr(user, "id", "unknown")
            user_name = getattr(user, "name", "Unknown")

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} | "
            f"User: {user_name} ({user_id}) | "
            f"IP: {self._get_client_ip(request)}"
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.3f}s | "
                f"User: {user_id}"
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.3f}s | "
                f"User: {user_id}"
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"
