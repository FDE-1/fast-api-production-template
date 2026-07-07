from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..dependencies import CurrentUserDep, ServiceDep, SessionDep
from ..models import User
from ..schemas import UserRead
from ..services import send_welcome_email
from ..utils.rate_limit import limiter
from ..utils.settings import settings

router = APIRouter(tags=["Users"])


@router.get("/users/{user_id}", response_model=UserRead)
@limiter.limit(settings.user_rate_limit)
async def read_user(
    request: Request,
    user_id: int,
    session: SessionDep,
    current: CurrentUserDep,
    service: ServiceDep,
    background_tasks: BackgroundTasks,
) -> User:
    """Return the user by the given user_id"""
    user = service.get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    background_tasks.add_task(send_welcome_email, f"{current.username}@example.com")
    return user
