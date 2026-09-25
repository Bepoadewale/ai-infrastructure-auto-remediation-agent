import os

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

app = FastAPI()
healthy = Gauge("checkout_fixture_healthy", "Whether checkout is healthy")


def is_broken() -> bool:
    return os.getenv("BROKEN", "0") == "1"


@app.get("/healthz")
def healthz(response: Response) -> dict[str, str]:
    if is_broken():
        response.status_code = 500
        return {"status": "broken"}
    return {"status": "ok"}


@app.get("/live")
def live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/ready")
def ready(response: Response) -> dict[str, str]:
    if is_broken():
        response.status_code = 503
        return {"status": "not-ready"}
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    healthy.set(0 if is_broken() else 1)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
