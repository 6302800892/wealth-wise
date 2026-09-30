"""Composition root: builds the FastAPI app and provides the single start command `poetry run wealthwise`."""

import logging
import shutil
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.errors import register_error_handlers
from src.api.middleware import correlation_middleware
from src.api.routers import ROUTERS, health
from src.config.clock import Clock, clock_for
from src.config.logging_config import configure_logging
from src.config.settings import PROJECT_ROOT, Settings, load_settings
from src.service.bootstrap import bootstrap
from src.service.scheduler import nav_refresh_loop

log = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    task = nav_refresh_loop(app.state.settings, app.state.clock)
    try:
        yield
    finally:
        if task is not None:
            task.cancel()


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    settings = settings or load_settings()
    clock = clock or clock_for(settings.business_date)
    bootstrap(settings, clock)
    app = FastAPI(title="WealthWise", version="1.0.0", lifespan=_lifespan)
    app.state.settings = settings
    app.state.clock = clock
    register_error_handlers(app)
    app.middleware("http")(correlation_middleware)
    app.include_router(health.router)
    for router in ROUTERS:
        app.include_router(router, prefix="/api/v1")
    dist = Path(settings.frontend_dist)
    if (dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=dist, html=True), name="ui")
    return app


def _build_frontend(settings: Settings) -> None:
    if (Path(settings.frontend_dist) / "index.html").is_file():
        return
    npm = shutil.which("npm")
    if npm is None:
        log.warning("frontend_not_built", extra={"reason": "npm not found; serving API only"})
        return
    frontend = str(PROJECT_ROOT / "frontend")
    subprocess.run([npm, "--prefix", frontend, "ci"], check=True)
    subprocess.run([npm, "--prefix", frontend, "run", "build"], check=True)


def run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    _build_frontend(settings)
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None, access_log=False)


if __name__ == "__main__":
    run()
