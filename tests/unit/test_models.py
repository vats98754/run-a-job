"""Job model tests."""

import pytest
from datetime import datetime
from run_a_job.scheduling.models import Job, JobStatus, JobType


@pytest.mark.unit
def test_job_creation():
    """Test job model creation."""
    job = Job(
        name="Test Job",
        job_type=JobType.BROWSER_AUTOMATION,
        function_name="test_function"
    )
    
    assert job.name == "Test Job"
    assert job.job_type == JobType.BROWSER_AUTOMATION
    assert job.function_name == "test_function"
    assert job.status == JobStatus.PENDING
    assert job.enabled is True
    assert job.run_count == 0


@pytest.mark.unit
def test_job_with_schedule():
    """Test job with schedule."""
    job = Job(
        name="Scheduled Job",
        job_type=JobType.WEBSITE_MONITORING,
        function_name="check_website",
        schedule="0 9 * * *"
    )
    
    assert job.schedule == "0 9 * * *"
    assert job.timezone == "UTC"


@pytest.mark.unit
def test_job_parameters():
    """Test job with parameters."""
    params = {"url": "https://example.com", "timeout": 30}
    job = Job(
        name="Parameterized Job",
        job_type=JobType.DATA_SCRAPING,
        function_name="scrape_data",
        parameters=params
    )
    
    assert job.parameters == params
    assert job.parameters["url"] == "https://example.com"