from typing import Optional

class RoutewayError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class RoutewayAuthError(RoutewayError):
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class RoutewayRateLimitError(RoutewayError):
    def __init__(self, message: str):
        super().__init__(message, status_code=429)


class RoutewayServerError(RoutewayError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code=status_code)


class RoutewayHTTPError(RoutewayError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message, status_code=status_code)


class RoutewayTimeoutError(RoutewayError):
    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)


class RoutewayConnectionError(RoutewayError):
    def __init__(self, message: str = "Connection failed"):
        super().__init__(message)

class RoutewayValidationError(RoutewayError):
    def __init__(self, message: str):
        super().__init__(message)


class RoutewayStreamError(RoutewayError):
    def __init__(self, message: str):
        super().__init__(message)