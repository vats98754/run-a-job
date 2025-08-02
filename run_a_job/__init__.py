"""
Run a Job - Automated Task Orchestration Platform

A comprehensive platform for browser automation, job scheduling, and task orchestration.
"""

__version__ = "0.1.0"
__author__ = "Run-a-Job Team"
__email__ = "team@run-a-job.com"

# Core imports for public API
from run_a_job.automation.browser import BrowserAutomation
from run_a_job.scheduling.scheduler import JobScheduler
from run_a_job.services.job_service import JobService
from run_a_job.config.settings import Settings

__all__ = [
    "BrowserAutomation",
    "JobScheduler", 
    "JobService",
    "Settings",
]