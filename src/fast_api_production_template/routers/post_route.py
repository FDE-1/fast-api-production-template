from fastapi import APIRouter, Request

from ..dependencies import CommonsDep, CurrentUserDep, ServiceDep, SessionDep
from ..models import Post
from ..schemas import PostRead
from ..utils.rate_limit import limiter
from ..utils.settings import settings

router = APIRouter(tags=["Posts"])


@router.get("/users/{user_id}/posts", response_model=list[PostRead])
@limiter.limit(settings.user_rate_limit)
async def read_user_posts(
    request: Request,
    user_id: int,
    commons: CommonsDep,
    session: SessionDep,
    service: ServiceDep,
    current: CurrentUserDep,
) -> list[Post]:
    """Return the list of post of a given user with the query"""
    return service.get_user_posts(
        session,
        user_id,
        skip=commons.skip,
        limit=commons.limit,
        q=commons.q,
        sort=commons.sort,
    )
