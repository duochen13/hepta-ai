"""
DataVint API Server - Main Application

FastAPI entry point with CORS middleware and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import playground, data, visualization, simple_profiling, code_playground

# Create FastAPI app
app = FastAPI(
    title="DataVint API",
    description="Data Quality Detection & Optimization API",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware - allows local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        # Production
        "https://datavint.io",
        "https://www.datavint.io",
        "https://api.datavint.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(playground.router, prefix="/api/playground", tags=["playground"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["visualization"])
app.include_router(simple_profiling.router, prefix="/api/profiling", tags=["profiling"])
app.include_router(code_playground.router, tags=["code-playground"])


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "DataVint API",
        "version": "0.2.0",
        "build": "af7543e-debug",  # Git commit hash for deployment verification
        "status": "healthy",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health():
    """Health check endpoint with debug info"""
    import os
    from pathlib import Path
    import datavint

    datavint_file = Path(datavint.__file__)
    project_root = datavint_file.parent.parent
    dataset_path = project_root / "raw_data/titanic/titanic.csv"

    return {
        "status": "healthy",
        "debug": {
            "cwd": os.getcwd(),
            "datavint_location": str(datavint_file),
            "project_root": str(project_root),
            "dataset_path": str(dataset_path),
            "dataset_exists": dataset_path.exists(),
            "paths_checked": {
                "/app/raw_data/titanic/titanic.csv": os.path.exists("/app/raw_data/titanic/titanic.csv"),
                "/app/server/raw_data/titanic/titanic.csv": os.path.exists("/app/server/raw_data/titanic/titanic.csv"),
            }
        }
    }


@app.get("/api/debug/paths")
async def debug_paths():
    """Debug endpoint to check filesystem paths"""
    import os
    import sys
    from pathlib import Path
    import datavint

    datavint_file = Path(datavint.__file__)
    project_root = datavint_file.parent.parent
    dataset_path = project_root / "raw_data/titanic/titanic.csv"

    return {
        "cwd": os.getcwd(),
        "datavint.__file__": str(datavint_file),
        "project_root": str(project_root),
        "dataset_path": str(dataset_path),
        "dataset_exists": dataset_path.exists(),
        "parent_dirs": {
            "/app": os.path.exists("/app"),
            "/app/raw_data": os.path.exists("/app/raw_data"),
            "/app/raw_data/titanic": os.path.exists("/app/raw_data/titanic"),
            "/app/raw_data/titanic/titanic.csv": os.path.exists("/app/raw_data/titanic/titanic.csv"),
        },
        "server_dirs": {
            "/app/server": os.path.exists("/app/server"),
            "/app/server/raw_data": os.path.exists("/app/server/raw_data"),
            "/app/server/raw_data/titanic": os.path.exists("/app/server/raw_data/titanic"),
            "/app/server/raw_data/titanic/titanic.csv": os.path.exists("/app/server/raw_data/titanic/titanic.csv"),
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
