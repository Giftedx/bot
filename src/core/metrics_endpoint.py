from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import asyncio
import logging

logger = logging.getLogger(__name__)


async def _run_server(app: FastAPI, port: int):
    """Run uvicorn server inside a background task."""
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def start_metrics_server(port: int = 8080):
    """Start a FastAPI server exposing /metrics in the background.

    This should be called once during application startup.
    """
    app = FastAPI()

    @app.get("/metrics")
    async def metrics():  # noqa: D401
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    loop = asyncio.get_event_loop()
    loop.create_task(_run_server(app, port))
    logger.info(f"Metrics endpoint available at http://0.0.0.0:{port}/metrics")
