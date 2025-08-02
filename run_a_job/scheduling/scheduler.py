"""Core job scheduler implementation using APScheduler."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
import traceback
import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import JobExecutionEvent, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from croniter import croniter

from run_a_job.config.settings import settings
from run_a_job.config.logging import get_logger
from run_a_job.scheduling.models import Job, JobStatus, JobRun, JobResult, JobType
from run_a_job.repositories.job_repository import JobRepository


logger = get_logger(__name__)


class JobScheduler:
    """Advanced job scheduler with persistent storage and monitoring."""
    
    def __init__(self, job_repository: Optional[JobRepository] = None):
        """Initialize the job scheduler.
        
        Args:
            job_repository: Optional job repository for persistence
        """
        self.job_repository = job_repository or JobRepository()
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.running = False
        self.job_functions: Dict[str, Callable] = {}
        
        # Job execution tracking
        self.active_jobs: Dict[str, JobRun] = {}
        
    async def start(self) -> None:
        """Start the job scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        try:
            # Configure job store
            jobstores = {
                'default': SQLAlchemyJobStore(url=settings.database_url)
            }
            
            # Configure executors
            executors = {
                'default': AsyncIOExecutor(max_workers=settings.max_concurrent_jobs)
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300  # 5 minutes
            }
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone=timezone.utc
            )
            
            # Add event listeners
            self.scheduler.add_listener(
                self._job_executed_listener, 
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
            )
            
            # Start scheduler
            self.scheduler.start()
            self.running = True
            
            # Load existing jobs from database
            await self._load_jobs_from_database()
            
            logger.info("Job scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
            
    async def stop(self) -> None:
        """Stop the job scheduler."""
        if not self.running:
            return
            
        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                
            self.running = False
            logger.info("Job scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            
    async def add_job(
        self,
        name: str,
        function_name: str,
        parameters: Dict[str, Any] = None,
        schedule: str = None,
        job_type: JobType = JobType.CUSTOM_SCRIPT,
        description: str = None,
        **kwargs
    ) -> str:
        """Add a new job to the scheduler.
        
        Args:
            name: Job name
            function_name: Name of the function to execute
            parameters: Function parameters
            schedule: Cron expression for scheduling
            job_type: Type of job
            description: Job description
            **kwargs: Additional job options
            
        Returns:
            Job ID
        """
        if not self.running:
            raise RuntimeError("Scheduler is not running")
            
        # Create job model
        job = Job(
            name=name,
            description=description,
            job_type=job_type,
            function_name=function_name,
            parameters=parameters or {},
            schedule=schedule,
            **kwargs
        )
        
        # Save to database
        await self.job_repository.create(job)
        
        # Add to scheduler if schedule is provided
        if schedule:
            await self._schedule_job(job)
            
        logger.info(f"Job '{name}' added with ID: {job.id}")
        return job.id
        
    async def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler.
        
        Args:
            job_id: ID of the job to remove
            
        Returns:
            True if job was removed, False otherwise
        """
        try:
            # Remove from scheduler
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                
            # Remove from database
            success = await self.job_repository.delete(job_id)
            
            if success:
                logger.info(f"Job {job_id} removed successfully")
            else:
                logger.warning(f"Job {job_id} not found in database")
                
            return success
            
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False
            
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job.
        
        Args:
            job_id: ID of the job to pause
            
        Returns:
            True if job was paused, False otherwise
        """
        try:
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.pause_job(job_id)
                
            # Update status in database
            job = await self.job_repository.get(job_id)
            if job:
                job.status = JobStatus.PAUSED
                job.enabled = False
                await self.job_repository.update(job)
                
            logger.info(f"Job {job_id} paused")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
            
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.
        
        Args:
            job_id: ID of the job to resume
            
        Returns:
            True if job was resumed, False otherwise
        """
        try:
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.resume_job(job_id)
                
            # Update status in database
            job = await self.job_repository.get(job_id)
            if job:
                job.status = JobStatus.PENDING
                job.enabled = True
                await self.job_repository.update(job)
                
            logger.info(f"Job {job_id} resumed")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
            
    async def run_job_now(self, job_id: str) -> str:
        """Execute a job immediately.
        
        Args:
            job_id: ID of the job to run
            
        Returns:
            Run ID
        """
        job = await self.job_repository.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        # Create job run
        job_run = JobRun(
            job_id=job_id,
            status=JobStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Execute job
        try:
            result = await self._execute_job(job, job_run)
            return job_run.id
            
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            raise
            
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job instance or None if not found
        """
        return await self.job_repository.get(job_id)
        
    async def list_jobs(
        self, 
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Job]:
        """List jobs with optional filtering.
        
        Args:
            status: Filter by status
            job_type: Filter by job type
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs
        """
        return await self.job_repository.list(
            status=status,
            job_type=job_type,
            limit=limit,
            offset=offset
        )
        
    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get the current status of a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status or None if not found
        """
        job = await self.job_repository.get(job_id)
        return job.status if job else None
        
    def register_function(self, name: str, func: Callable) -> None:
        """Register a function that can be called by jobs.
        
        Args:
            name: Function name
            func: Function to register
        """
        self.job_functions[name] = func
        logger.info(f"Function '{name}' registered")
        
    async def _schedule_job(self, job: Job) -> None:
        """Schedule a job in APScheduler."""
        if not job.schedule:
            return
            
        try:
            # Validate cron expression
            if not croniter.is_valid(job.schedule):
                raise ValueError(f"Invalid cron expression: {job.schedule}")
                
            # Calculate next run time
            cron = croniter(job.schedule, datetime.utcnow())
            next_run = cron.get_next(datetime)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_job_wrapper,
                args=[job.id],
                trigger='cron',
                **self._parse_cron_expression(job.schedule),
                id=job.id,
                name=job.name,
                max_instances=job.max_instances,
                replace_existing=True
            )
            
            # Update next run time in database
            job.next_run = next_run
            await self.job_repository.update(job)
            
            logger.info(f"Job '{job.name}' scheduled with cron: {job.schedule}")
            
        except Exception as e:
            logger.error(f"Error scheduling job {job.id}: {e}")
            raise
            
    async def _execute_job_wrapper(self, job_id: str) -> None:
        """Wrapper for job execution that handles APScheduler integration."""
        job = await self.job_repository.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
            
        # Create job run
        job_run = JobRun(
            job_id=job_id,
            status=JobStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        await self._execute_job(job, job_run)
        
    async def _execute_job(self, job: Job, job_run: JobRun) -> JobResult:
        """Execute a job and return the result."""
        start_time = datetime.utcnow()
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.last_run = start_time
            job.run_count += 1
            await self.job_repository.update(job)
            
            # Track active job
            self.active_jobs[job_run.id] = job_run
            
            # Get function to execute
            if job.function_name not in self.job_functions:
                raise ValueError(f"Function '{job.function_name}' not registered")
                
            func = self.job_functions[job.function_name]
            
            # Execute function
            logger.info(f"Executing job '{job.name}' (ID: {job.id})")
            
            if asyncio.iscoroutinefunction(func):
                result = await func(**job.parameters)
            else:
                result = func(**job.parameters)
                
            # Calculate duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Update job status
            job.status = JobStatus.COMPLETED
            job.success_count += 1
            await self.job_repository.update(job)
            
            # Create result
            job_result = JobResult(
                job_id=job.id,
                run_id=job_run.id,
                status=JobStatus.COMPLETED,
                started_at=start_time,
                completed_at=end_time,
                duration=duration,
                data=result if isinstance(result, dict) else {"result": result}
            )
            
            logger.info(f"Job '{job.name}' completed successfully in {duration:.2f}s")
            return job_result
            
        except Exception as e:
            # Calculate duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Update job status
            job.status = JobStatus.FAILED
            job.failure_count += 1
            await self.job_repository.update(job)
            
            # Get error details
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            
            # Create result
            job_result = JobResult(
                job_id=job.id,
                run_id=job_run.id,
                status=JobStatus.FAILED,
                started_at=start_time,
                completed_at=end_time,
                duration=duration,
                error=error_msg,
                logs=[error_traceback]
            )
            
            logger.error(f"Job '{job.name}' failed: {error_msg}")
            return job_result
            
        finally:
            # Remove from active jobs
            self.active_jobs.pop(job_run.id, None)
            
    async def _load_jobs_from_database(self) -> None:
        """Load existing jobs from database and schedule them."""
        try:
            jobs = await self.job_repository.list(enabled=True)
            
            for job in jobs:
                if job.schedule:
                    await self._schedule_job(job)
                    
            logger.info(f"Loaded {len(jobs)} jobs from database")
            
        except Exception as e:
            logger.error(f"Error loading jobs from database: {e}")
            
    def _parse_cron_expression(self, cron_expr: str) -> Dict[str, Any]:
        """Parse cron expression into APScheduler trigger kwargs."""
        parts = cron_expr.split()
        
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts")
            
        minute, hour, day, month, day_of_week = parts
        
        kwargs = {}
        
        if minute != '*':
            kwargs['minute'] = minute
        if hour != '*':
            kwargs['hour'] = hour
        if day != '*':
            kwargs['day'] = day
        if month != '*':
            kwargs['month'] = month
        if day_of_week != '*':
            kwargs['day_of_week'] = day_of_week
            
        return kwargs
        
    def _job_executed_listener(self, event: JobExecutionEvent) -> None:
        """Listen for job execution events."""
        if event.exception:
            logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} executed successfully")