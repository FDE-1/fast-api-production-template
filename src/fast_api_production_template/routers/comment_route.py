from fastapi import APIRouter, Request

from ..dependencies import CommonsDep, CurrentUserDep, ServiceDep, SessionDep
from ..models import Comment
from ..schemas import CommentRead
from ..utils.rate_limit import limiter
from ..utils.settings import settings

router = APIRouter(tags=["Comments"])


@router.get("/posts/{post_id}/comments", response_model=list[CommentRead])
@limiter.limit(settings.user_rate_limit)
async def read_post_comments(
    request: Request,
    post_id: int,
    commons: CommonsDep,
    session: SessionDep,
    service: ServiceDep,
    current: CurrentUserDep,
) -> list[Comment]:
    """Return the list of commewnts of a given post with the query"""
    return service.get_post_comments(
        session,
        post_id,
        skip=commons.skip,
        limit=commons.limit,
        q=commons.q,
        sort=commons.sort,
    )
