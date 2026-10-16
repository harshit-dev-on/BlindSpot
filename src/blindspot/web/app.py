"""FastAPI web application factory and static asset mounting for BlindSpot."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from blindspot.web.router import api_router


def create_app() -> FastAPI:
    """Build and configure the BlindSpot web demonstration FastAPI application."""
    app = FastAPI(
        title="BlindSpot UX Testing Studio",
        version="0.1.0",
        description="Autonomous AI-Powered Website UX & Usability Testing Engine",
    )

    # Enable local CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    app.include_router(api_router)

    # Mount static assets
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        """Serve the interactive web demonstration interface."""
        index_file = static_dir / "index.html"
        if not index_file.exists():
            return {"message": "BlindSpot Web API is online. Frontend static files are loading."}
        return FileResponse(index_file, media_type="text/html")

    return app


# Default ASGI application instance for uvicorn
app = create_app()
