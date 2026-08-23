"""Erros seguros para a API de checkout."""


class CheckoutError(Exception):
    status_code = 400
    code = "CHECKOUT_ERROR"

    def __init__(self, message: str = "Não foi possível processar a solicitação.") -> None:
        super().__init__(message)
        self.message = message


class ValidationError(CheckoutError):
    code = "VALIDATION_ERROR"


class NotFoundError(CheckoutError):
    status_code = 404
    code = "NOT_FOUND"


class AuthorizationError(CheckoutError):
    status_code = 401
    code = "UNAUTHORIZED"


class ConflictError(CheckoutError):
    status_code = 409
    code = "IDEMPOTENCY_CONFLICT"


class GatewayConfigurationError(CheckoutError):
    status_code = 503
    code = "PAYMENT_UNAVAILABLE"


class GatewayError(CheckoutError):
    status_code = 502
    code = "PAYMENT_PROVIDER_ERROR"
