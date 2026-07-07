from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)
REQUEST_TIME = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)


def setup_metrics_middleware(app: FastAPI) -> None:
    """Register the Prometheus request-instrumentation middleware."""

    @app.middleware("http")
    async def prometheus_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.monotonic()
        http_status = 500
        try:
            response = await call_next(request)
            http_status = response.status_code
            return response
        finally:
            process_time = time.monotonic() - start_time

            route = request.scope.get("route")
            if route:
                endpoint = route.path
            else:
                endpoint = "unmatched_path"

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                http_status=http_status,
            ).inc()

            REQUEST_TIME.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(process_time)
