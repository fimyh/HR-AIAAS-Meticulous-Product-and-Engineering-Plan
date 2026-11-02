from typing import NoReturn

from fastapi import HTTPException, status


def not_implemented(feature: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "FEATURE_NOT_IMPLEMENTED",
            "message": f"{feature} is defined in the API contract but is not implemented yet.",
        },
    )
