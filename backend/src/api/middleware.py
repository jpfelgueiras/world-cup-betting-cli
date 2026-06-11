"""
API Middleware for monitoring and observability.

Includes:
- Prometheus metrics collection
- Request logging
- Performance tracking
"""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram

# =============================================================================
# Prometheus Metrics
# =============================================================================

# Request counters
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# Request latency histogram
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Active requests gauge
ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Number of active HTTP requests",
)

# Error counter
ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"],
)


async def prometheus_middleware(request: Request, call_next: Callable) -> Response:
    """
    Collect Prometheus metrics for all requests.

    Tracks:
    - Request count by method, endpoint, status
    - Request latency
    - Active requests
    - Error count by type
    """
    start_time = time.time()
    ACTIVE_REQUESTS.inc()

    endpoint = request.url.path
    method = request.method

    try:
        response = await call_next(request)

        # Record metrics
        status = str(response.status_code)
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()

        # Track errors (4xx and 5xx)
        if response.status_code >= 400:
            error_type = "client_error" if response.status_code < 500 else "server_error"
            ERROR_COUNT.labels(method=method, endpoint=endpoint, error_type=error_type).inc()

        return response

    except Exception:
        # Record error
        ERROR_COUNT.labels(method=method, endpoint=endpoint, error_type="exception").inc()
        raise

    finally:
        # Record latency
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
        ACTIVE_REQUESTS.dec()


async def metrics_endpoint(request: Request) -> Response:
    """
    Expose Prometheus metrics endpoint.

    Returns metrics in Prometheus text exposition format.
    Should be scraped by Prometheus server.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)
