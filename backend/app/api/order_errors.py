"""Turn cart and order errors into HTTP errors with a machine-readable `code`.

The UI reads `code` to decide what to ask: "Add anyway?" for a conflict,
"Start a new cart?" for another restaurant.
"""

from fastapi import HTTPException

from app.orders.errors import (
    InvalidChoice,
    LineConflict,
    NotFound,
    OrderError,
    OtherRestaurant,
)


def http_error(exc: OrderError) -> HTTPException:
    detail: dict[str, object] = {"code": exc.code, "message": exc.message}
    if isinstance(exc, LineConflict):
        detail["reasons"] = exc.reasons
    if isinstance(exc, OtherRestaurant):
        detail["restaurant"] = exc.restaurant
    status = 404 if isinstance(exc, NotFound) else 422 if isinstance(exc, InvalidChoice) else 409
    return HTTPException(status_code=status, detail=detail)
