import time
import uuid
import asyncio
from collections import defaultdict, deque

import structlog
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator


# -----------------------------
# Structlog Configuration
# -----------------------------
# structlog.configure(
#     processors=[
#         structlog.stdlib.add_log_level,
#         structlog.stdlib.add_logger_name,
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.processors.JSONRenderer(),
#     ],
#     wrapper_class=structlog.BoundLogger,
#     logger_factory=structlog.PrintLoggerFactory(),
# )

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="EY Payment API",
    version="1.0.0",
    description="FastAPI Middleware Observability Demo"
)


# -----------------------------
# Prometheus Metrics
# -----------------------------
PAYMENT_AMOUNT = Histogram(
    "payment_amount_gbp",
    "Payment amount in GBP",
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

ERROR_COUNT = Counter(
    "payment_errors_total",
    "Total payment processing errors",
    ["error_type"]
)

RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total",
    "Total number of rate limit hits",
    ["client_ip"]
)

REQUEST_LATENCY = Histogram(
    "custom_request_latency_ms",
    "Request latency in milliseconds",
    ["path", "method"]
)


# Auto instrument FastAPI app
Instrumentator().instrument(app).expose(app)


# -----------------------------
# Rate Limiting Middleware
# 100 requests per 60 seconds per IP
# -----------------------------
RATE_LIMIT = 100
WINDOW_SECONDS = 60

client_requests = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()

    request_times = client_requests[client_ip]

    while request_times and current_time - request_times[0] > WINDOW_SECONDS:
        request_times.popleft()

    if len(request_times) >= RATE_LIMIT:
        RATE_LIMIT_HITS.labels(client_ip=client_ip).inc()

        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": "Rate limit exceeded. Please try again later."
            },
            headers={"Retry-After": str(WINDOW_SECONDS)}
        )

    request_times.append(current_time)

    return await call_next(request)


# -----------------------------
# Logging Middleware
# -----------------------------
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    start_time = time.perf_counter()

    log.info(
        "request.started",
        path=request.url.path,
        method=request.method,
        correlation_id=correlation_id
    )

    try:
        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        REQUEST_LATENCY.labels(
            path=request.url.path,
            method=request.method
        ).observe(latency_ms)

        log.info(
            "request.completed",
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            latency_ms=latency_ms,
            correlation_id=correlation_id
        )

        response.headers["X-Correlation-Id"] = correlation_id
        return response

    except Exception as e:
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()

        log.error(
            "request.failed",
            path=request.url.path,
            method=request.method,
            error=str(e),
            correlation_id=correlation_id
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "correlation_id": correlation_id
            },
            headers={"X-Correlation-Id": correlation_id}
        )


# -----------------------------
# Health Check APIs
# -----------------------------
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    return {
        "status": "ready",
        "db": "ok",
        "mq": "ok"
    }


# -----------------------------
# Retry Logic with Tenacity
# -----------------------------
fraud_api_call_count = 0


async def flaky_fraud_check(payload: dict) -> dict:
    global fraud_api_call_count

    fraud_api_call_count += 1

    if fraud_api_call_count < 3:
        print(f"Attempt {fraud_api_call_count}: Fraud API timeout")
        raise ConnectionError("Fraud API timeout")

    print(f"Attempt {fraud_api_call_count}: Fraud check passed")

    return {
        "fraud_score": 0.02,
        "decision": "approved"
    }


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=0.1, max=2),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
async def call_fraud_api_with_retry(payload: dict) -> dict:
    return await flaky_fraud_check(payload)


@app.post("/fraud/retry-test")
async def retry_test(payload: dict):
    global fraud_api_call_count

    fraud_api_call_count = 0

    try:
        result = await call_fraud_api_with_retry(payload)
        return {
            "message": "Fraud API call successful after retry",
            "result": result
        }

    except Exception as e:
        ERROR_COUNT.labels(error_type="retry_failed").inc()
        return JSONResponse(
            status_code=500,
            content={
                "message": "Fraud API failed after retries",
                "error": str(e)
            }
        )


# -----------------------------
# Circuit Breaker with PyBreaker
# -----------------------------
class LoggingListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        log.warning(
            "circuit_breaker.state_change",
            breaker=cb.name,
            old=str(old_state),
            new=str(new_state)
        )


fraud_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    listeners=[LoggingListener()],
    name="fraud-api"
)


def failing_fraud_service(payload: dict) -> dict:
    raise ConnectionError("Fraud service is down")


def safe_fraud_check(payload: dict) -> dict:
    try:
        return fraud_breaker.call(failing_fraud_service, payload)

    except pybreaker.CircuitBreakerError:
        ERROR_COUNT.labels(error_type="circuit_open").inc()

        return {
            "fraud_score": None,
            "decision": "manual_review",
            "circuit": "open"
        }

    except Exception as e:
        ERROR_COUNT.labels(error_type="fraud_service_error").inc()

        return {
            "fraud_score": None,
            "decision": "error",
            "reason": str(e),
            "circuit": fraud_breaker.current_state
        }


@app.post("/fraud/circuit-test")
async def circuit_test(payload: dict):
    result = safe_fraud_check(payload)

    return {
        "message": "Circuit breaker test completed",
        "result": result,
        "circuit_state": fraud_breaker.current_state
    }


# -----------------------------
# Payment API
# -----------------------------
@app.post("/payments")
async def create_payment(request: Request):
    body = await request.json()

    amount = body.get("amount", 0)
    currency = body.get("currency", "GBP")

    if currency == "GBP":
        PAYMENT_AMOUNT.observe(amount)

    log.info(
        "payment.received",
        amount=amount,
        currency=currency
    )

    fraud_result = await call_fraud_api_with_retry(body)

    return {
        "payment_id": str(uuid.uuid4()),
        "status": "accepted",
        "fraud_check": fraud_result,
        **body
    }


# -----------------------------
# Custom Metrics Endpoint
# -----------------------------
@app.get("/custom-metrics")
async def custom_metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# -----------------------------
# Root Endpoint
# -----------------------------
@app.get("/")
async def root():
    return {
        "message": "EY Payment API is running",
        "docs": "/docs",
        "health": "/health/ready",
        "metrics": "/metrics"
    }