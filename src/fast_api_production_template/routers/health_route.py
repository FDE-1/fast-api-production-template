from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..dependencies import SessionDep
from ..utils.rate_limit import limiter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
@limiter.exempt  # type: ignore[untyped-decorator]
async def liveness(request: Request) -> dict[str, str]:
    """Check if app is live."""
    return {"status": "alive"}


@router.get("/ready")
@limiter.exempt  # type: ignore[untyped-decorator]
async def readiness(request: Request, session: SessionDep) -> dict[str, str]:
    """readiness api"""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc
    return {"status": "ready"}
