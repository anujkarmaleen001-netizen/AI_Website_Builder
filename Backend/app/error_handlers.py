"""
Centralized error handling and custom exceptions for production.
"""
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class BaseAPIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Application-specific error code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)


class RateLimitExceeded(BaseAPIException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        """
        Initialize rate limit exception.
        
        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,

            
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )
        self.retry_after = retry_after


class ExternalAPIError(BaseAPIException):
    """Exception raised when external API calls fail."""
    
    def __init__(
        self,
        service: str,
        message: str,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize external API error.
        
        Args:
            service: Name of the external service
            message: Error message
            original_error: Original exception if available
        """
        details = {"service": service}
        if original_error:
            details["original_error"] = str(original_error)
        
        super().__init__(
            message=f"{service} API error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_API_ERROR",
            details=details
        )


class CircuitBreakerOpenError(BaseAPIException):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, service: str, message: str = "Service temporarily unavailable"):
        """
        Initialize circuit breaker error.
        
        Args:
            service: Name of the service
            message: Error message
        """
        super().__init__(
            message=f"{message}: {service}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="CIRCUIT_BREAKER_OPEN",
            details={"service": service}
        )


class ValidationError(BaseAPIException):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
        """
        details = {}
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ResourceNotFoundError(BaseAPIException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        """
        Initialize resource not found error.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
        """
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class TimeoutError(BaseAPIException):
    """Exception raised when an operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: int):
        """
        Initialize timeout error.
        
        Args:
            operation: Name of the operation that timed out
            timeout_seconds: Timeout duration in seconds
        """
        super().__init__(
            message=f"Operation timed out: {operation} (after {timeout_seconds}s)",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            error_code="TIMEOUT_ERROR",
            details={"operation": operation, "timeout_seconds": timeout_seconds}
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Application-specific error code
        details: Additional error details
        correlation_id: Request correlation ID
        
    Returns:
        JSONResponse with error details
    """
    error_response = {
        "error": {
            "message": message,
            "code": error_code or f"ERR_{status_code}",
            "status": status_code
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if correlation_id:
        error_response["correlation_id"] = correlation_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    Handler for BaseAPIException.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse with error details
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    
    # Log the error
    logger.error(
        f"API Exception: {exc.message}",
        extra={
            'extra_fields': {
                'error_code': exc.error_code,
                'status_code': exc.status_code,
                'details': exc.details,
                'correlation_id': correlation_id
            }
        }
    )
    
    return create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        correlation_id=correlation_id
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for HTTPException.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse with error details
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    
    logger.error(
        f"HTTP Exception: {exc.detail}",
        extra={
            'extra_fields': {
                'status_code': exc.status_code,
                'correlation_id': correlation_id
            }
        }
    )
    
    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        correlation_id=correlation_id
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for RequestValidationError.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse with validation errors
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Validation Error",
        extra={
            'extra_fields': {
                'errors': errors,
                'correlation_id': correlation_id
            }
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation error",
        error_code="VALIDATION_ERROR",
        details={"errors": errors},
        correlation_id=correlation_id
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unexpected exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse with error details
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    
    # Log the unexpected error with full traceback
    logger.exception(
        "Unexpected error",
        extra={
            'extra_fields': {
                'exception_type': type(exc).__name__,
                'correlation_id': correlation_id
            }
        }
    )
    
    # Don't expose internal error details in production
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        correlation_id=correlation_id
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
