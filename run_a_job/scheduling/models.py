"""Job scheduling models and data structures."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobType(str, Enum):
    """Type of job."""
    BROWSER_AUTOMATION = "browser_automation"
    ACCOUNT_CREATION = "account_creation"
    WEBSITE_MONITORING = "website_monitoring"
    DATA_SCRAPING = "data_scraping"
    CUSTOM_SCRIPT = "custom_script"


class Job(BaseModel):
    """Job model representing a scheduled task."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    
    # Scheduling
    schedule: Optional[str] = None  # Cron expression
    timezone: str = "UTC"
    max_instances: int = 1
    
    # Execution parameters
    function_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = 3600  # seconds
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    # Results tracking
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # Configuration
    enabled: bool = True
    tags: List[str] = Field(default_factory=list)
    priority: int = 0  # Higher numbers = higher priority
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class JobRun(BaseModel):
    """Individual job execution record."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    job_id: str
    status: JobStatus
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    
    # Results
    result: Optional[Any] = None
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    
    # Execution context
    worker_id: Optional[str] = None
    attempt: int = 1
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class JobResult(BaseModel):
    """Result of a job execution."""
    
    job_id: str
    run_id: str
    status: JobStatus
    
    # Timing information
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Result data
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    
    # Metrics
    bytes_processed: Optional[int] = None
    records_processed: Optional[int] = None
    urls_visited: Optional[int] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ScheduleTemplate(BaseModel):
    """Template for creating scheduled jobs."""
    
    name: str
    description: str
    job_type: JobType
    function_name: str
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    default_schedule: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True