"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from run_a_job.config.settings import settings


app = FastAPI(
    title="Run-a-Job API",
    description="Automated task orchestration platform",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Run-a-Job API is running", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


# Additional API routes will be added here
# from run_a_job.api.routes import jobs, scheduler
# app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
# app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])