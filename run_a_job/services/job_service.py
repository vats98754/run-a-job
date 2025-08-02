"""Job service for business logic operations."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from run_a_job.scheduling.scheduler import JobScheduler
from run_a_job.scheduling.models import Job, JobStatus, JobType, JobResult
from run_a_job.repositories.job_repository import JobRepository
from run_a_job.llm.workflow_translator import WorkflowTranslator
from run_a_job.config.logging import get_logger


logger = get_logger(__name__)


class JobService:
    """High-level service for job management operations."""
    
    def __init__(
        self,
        scheduler: Optional[JobScheduler] = None,
        job_repository: Optional[JobRepository] = None,
        workflow_translator: Optional[WorkflowTranslator] = None
    ):
        """Initialize job service.
        
        Args:
            scheduler: Job scheduler instance
            job_repository: Job repository instance
            workflow_translator: Workflow translator instance
        """
        self.scheduler = scheduler or JobScheduler()
        self.job_repository = job_repository or JobRepository()
        self.workflow_translator = workflow_translator or WorkflowTranslator()
        
    async def create_job_from_description(
        self,
        description: str,
        name: Optional[str] = None,
        schedule: Optional[str] = None
    ) -> str:
        """Create a job from natural language description.
        
        Args:
            description: Natural language description of the task
            name: Optional job name (auto-generated if not provided)
            schedule: Optional cron schedule
            
        Returns:
            Job ID
        """
        try:
            # Translate description to workflow
            workflow = await self.workflow_translator.translate(description)
            
            # Override with provided values
            if name:
                workflow["name"] = name
            if schedule:
                workflow["schedule"] = schedule
                
            # Create job
            job_id = await self.create_job_from_workflow(workflow)
            
            logger.info(f"Job created from description: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating job from description: {e}")
            raise
            
    async def create_job_from_workflow(self, workflow: Dict[str, Any]) -> str:
        """Create a job from workflow configuration.
        
        Args:
            workflow: Workflow configuration dictionary
            
        Returns:
            Job ID
        """
        try:
            # Extract job configuration
            job_config = {
                "name": workflow.get("name", "Unnamed Job"),
                "description": workflow.get("description"),
                "job_type": JobType(workflow.get("job_type", "custom_script")),
                "function_name": workflow["function_name"],
                "parameters": workflow.get("parameters", {}),
                "schedule": workflow.get("schedule"),
                "tags": workflow.get("tags", [])
            }
            
            # Create job using scheduler
            job_id = await self.scheduler.add_job(**job_config)
            
            logger.info(f"Job created from workflow: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating job from workflow: {e}")
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
        
    async def run_job_now(self, job_id: str) -> str:
        """Execute a job immediately.
        
        Args:
            job_id: Job ID to execute
            
        Returns:
            Run ID
        """
        try:
            if not self.scheduler.running:
                await self.scheduler.start()
                
            run_id = await self.scheduler.run_job_now(job_id)
            
            logger.info(f"Job {job_id} executed immediately with run ID: {run_id}")
            return run_id
            
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            raise
            
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job.
        
        Args:
            job_id: Job ID to pause
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.scheduler.running:
                await self.scheduler.start()
                
            success = await self.scheduler.pause_job(job_id)
            
            if success:
                logger.info(f"Job {job_id} paused successfully")
            else:
                logger.warning(f"Failed to pause job {job_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
            
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.
        
        Args:
            job_id: Job ID to resume
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.scheduler.running:
                await self.scheduler.start()
                
            success = await self.scheduler.resume_job(job_id)
            
            if success:
                logger.info(f"Job {job_id} resumed successfully")
            else:
                logger.warning(f"Failed to resume job {job_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
            
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.scheduler.running:
                success = await self.scheduler.remove_job(job_id)
            else:
                success = await self.job_repository.delete(job_id)
                
            if success:
                logger.info(f"Job {job_id} deleted successfully")
            else:
                logger.warning(f"Job {job_id} not found for deletion")
                
            return success
            
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
            
    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get the current status of a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status or None if not found
        """
        job = await self.job_repository.get(job_id)
        return job.status if job else None
        
    async def search_jobs(self, query: str, limit: int = 50) -> List[Job]:
        """Search jobs by name or description.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching jobs
        """
        return await self.job_repository.search_jobs(query, limit)
        
    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get overall job statistics.
        
        Returns:
            Dictionary with job statistics
        """
        try:
            # Get counts by status
            stats = {
                "total_jobs": 0,
                "by_status": {},
                "by_type": {},
                "active_jobs": 0,
                "successful_runs": 0,
                "failed_runs": 0
            }
            
            # Get all jobs
            all_jobs = await self.job_repository.list(limit=10000)
            stats["total_jobs"] = len(all_jobs)
            
            # Calculate statistics
            for job in all_jobs:
                # Count by status
                status = job.status
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                # Count by type
                job_type = job.job_type
                stats["by_type"][job_type] = stats["by_type"].get(job_type, 0) + 1
                
                # Count active jobs
                if job.enabled and job.status not in [JobStatus.CANCELLED, JobStatus.FAILED]:
                    stats["active_jobs"] += 1
                    
                # Sum run counts
                stats["successful_runs"] += job.success_count
                stats["failed_runs"] += job.failure_count
                
            return stats
            
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            raise
            
    async def update_job_configuration(
        self,
        job_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update job configuration.
        
        Args:
            job_id: Job ID to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job = await self.job_repository.get(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found for update")
                return False
                
            # Update allowed fields
            allowed_fields = {
                "name", "description", "schedule", "parameters",
                "timeout", "max_retries", "retry_delay", "enabled",
                "tags", "priority"
            }
            
            updated = False
            for field, value in updates.items():
                if field in allowed_fields and hasattr(job, field):
                    setattr(job, field, value)
                    updated = True
                    
            if updated:
                job.updated_at = datetime.utcnow()
                await self.job_repository.update(job)
                
                # Update in scheduler if running
                if self.scheduler.running and job.schedule:
                    await self.scheduler._schedule_job(job)
                    
                logger.info(f"Job {job_id} configuration updated")
                return True
            else:
                logger.warning(f"No valid fields to update for job {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False
            
    async def clone_job(self, job_id: str, new_name: Optional[str] = None) -> str:
        """Clone an existing job.
        
        Args:
            job_id: ID of job to clone
            new_name: Optional new name for cloned job
            
        Returns:
            New job ID
        """
        try:
            original_job = await self.job_repository.get(job_id)
            if not original_job:
                raise ValueError(f"Job {job_id} not found")
                
            # Create workflow from original job
            workflow = {
                "name": new_name or f"{original_job.name} (Copy)",
                "description": original_job.description,
                "job_type": original_job.job_type,
                "function_name": original_job.function_name,
                "parameters": original_job.parameters.copy(),
                "schedule": original_job.schedule,
                "tags": original_job.tags.copy()
            }
            
            # Create new job
            new_job_id = await self.create_job_from_workflow(workflow)
            
            logger.info(f"Job {job_id} cloned to {new_job_id}")
            return new_job_id
            
        except Exception as e:
            logger.error(f"Error cloning job {job_id}: {e}")
            raise