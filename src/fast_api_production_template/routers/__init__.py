from . import auth_route as auth
from . import comment_route as comments
from . import health_route as health
from . import metrics_route as metrics
from . import post_route as posts
from . import user_route as users

__all__ = ["auth", "comments", "health", "metrics", "posts", "users"]
