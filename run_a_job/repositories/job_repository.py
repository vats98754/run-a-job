"""Job repository for database operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Table, Column, String, Text, Integer, Boolean, DateTime, JSON

from run_a_job.repositories.base import BaseRepository, metadata
from run_a_job.scheduling.models import Job, JobStatus, JobType


# Job table definition
jobs_table = Table(
    'jobs',
    metadata,
    Column('id', String(36), primary_key=True),
    Column('name', String(255), nullable=False),
    Column('description', Text),
    Column('job_type', String(50), nullable=False),
    Column('status', String(20), nullable=False, default='pending'),
    
    # Scheduling
    Column('schedule', String(100)),
    Column('timezone', String(50), default='UTC'),
    Column('max_instances', Integer, default=1),
    
    # Execution parameters
    Column('function_name', String(255), nullable=False),
    Column('parameters', Text),  # JSON serialized
    Column('timeout', Integer, default=3600),
    Column('max_retries', Integer, default=3),
    Column('retry_delay', Integer, default=60),
    
    # Metadata
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('last_run', DateTime),
    Column('next_run', DateTime),
    
    # Results tracking
    Column('run_count', Integer, default=0),
    Column('success_count', Integer, default=0),
    Column('failure_count', Integer, default=0),
    
    # Configuration
    Column('enabled', Boolean, default=True),
    Column('tags', Text),  # JSON serialized list
    Column('priority', Integer, default=0),
)


class JobRepository(BaseRepository[Job]):
    """Repository for job data operations."""
    
    def __init__(self):
        """Initialize job repository."""
        super().__init__(Job)
        
    def _get_table(self):
        """Get the jobs table."""
        return jobs_table
        
    def _model_to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert job model to dictionary for database storage."""
        data = job.dict()
        
        # Serialize JSON fields
        data['parameters'] = self._serialize_json_field(data['parameters'])
        data['tags'] = self._serialize_json_field(data['tags'])
        
        return data
        
    def _dict_to_model(self, data: Dict[str, Any]) -> Job:
        """Convert dictionary from database to job model."""
        # Deserialize JSON fields
        if 'parameters' in data:
            data['parameters'] = self._deserialize_json_field(data['parameters']) or {}
        if 'tags' in data:
            data['tags'] = self._deserialize_json_field(data['tags']) or []
            
        return Job(**data)
        
    async def list(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Job]:
        """List jobs with filtering options.
        
        Args:
            status: Filter by job status
            job_type: Filter by job type
            enabled: Filter by enabled status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of jobs
        """
        filters = {}
        
        if status is not None:
            filters['status'] = status.value if isinstance(status, JobStatus) else status
        if job_type is not None:
            filters['job_type'] = job_type.value if isinstance(job_type, JobType) else job_type
        if enabled is not None:
            filters['enabled'] = enabled
            
        return await super().list(limit=limit, offset=offset, **filters)
        
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get all jobs with a specific status.
        
        Args:
            status: Job status to filter by
            
        Returns:
            List of jobs with the specified status
        """
        return await self.list(status=status, limit=1000)
        
    async def get_enabled_jobs(self) -> List[Job]:
        """Get all enabled jobs.
        
        Returns:
            List of enabled jobs
        """
        return await self.list(enabled=True, limit=1000)
        
    async def get_jobs_by_type(self, job_type: JobType) -> List[Job]:
        """Get all jobs of a specific type.
        
        Args:
            job_type: Job type to filter by
            
        Returns:
            List of jobs of the specified type
        """
        return await self.list(job_type=job_type, limit=1000)
        
    async def search_jobs(self, query: str, limit: int = 50) -> List[Job]:
        """Search jobs by name or description.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching jobs
        """
        try:
            async with self.session_factory() as session:
                table = self._get_table()
                
                # Build search query
                search_filter = (
                    table.c.name.ilike(f"%{query}%") |
                    table.c.description.ilike(f"%{query}%")
                )
                
                stmt = (
                    table.select()
                    .where(search_filter)
                    .limit(limit)
                )
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                jobs = []
                for row in rows:
                    data = dict(row._mapping)
                    jobs.append(self._dict_to_model(data))
                    
                return jobs
                
        except Exception as e:
            self.logger.error(f"Error searching jobs: {e}")
            raise
            
    async def update_job_stats(
        self,
        job_id: str,
        run_count_increment: int = 1,
        success: bool = True
    ) -> None:
        """Update job execution statistics.
        
        Args:
            job_id: Job ID
            run_count_increment: Amount to increment run count
            success: Whether the execution was successful
        """
        try:
            job = await self.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
                
            job.run_count += run_count_increment
            job.last_run = datetime.utcnow()
            
            if success:
                job.success_count += 1
            else:
                job.failure_count += 1
                
            await self.update(job)
            
        except Exception as e:
            self.logger.error(f"Error updating job stats for {job_id}: {e}")
            raise