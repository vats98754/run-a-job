"""
Run-a-Job Platform Examples

This file demonstrates the key capabilities of the run-a-job automation platform.
"""

import asyncio
from run_a_job import JobScheduler, BrowserAutomation, JobService
from run_a_job.llm.workflow_translator import WorkflowTranslator
from run_a_job.scheduling.models import JobType


async def demo_basic_browser_automation():
    """Demonstrate basic browser automation capabilities."""
    print("=== Browser Automation Demo ===")
    
    async with BrowserAutomation() as browser:
        # Navigate to a website
        await browser.navigate("https://httpbin.org/html")
        
        # Take a screenshot
        screenshot = await browser.take_screenshot()
        print(f"Screenshot taken: {len(screenshot)} bytes")
        
        # Get page title
        title = await browser.execute_script("return document.title")
        print(f"Page title: {title}")


async def demo_workflow_translation():
    """Demonstrate natural language to workflow translation."""
    print("\n=== Workflow Translation Demo ===")
    
    translator = WorkflowTranslator()
    
    examples = [
        "Check for Oasis concert tickets every hour",
        "Create 5 Twitter accounts daily at 9 AM",
        "Monitor visa appointments on vfsglobal.com every morning",
        "Scrape product prices from Amazon weekly"
    ]
    
    for description in examples:
        print(f"\nInput: '{description}'")
        workflow = await translator.translate(description)
        print(f"  Type: {workflow['job_type']}")
        print(f"  Function: {workflow['function_name']}")
        print(f"  Schedule: {workflow.get('schedule', 'None')}")
        print(f"  Tags: {workflow.get('tags', [])}")


async def demo_job_creation():
    """Demonstrate job creation and management."""
    print("\n=== Job Management Demo ===")
    
    job_service = JobService()
    
    # Create a job from natural language
    job_id = await job_service.create_job_from_description(
        "Check for concert tickets every 30 minutes",
        name="Concert Ticket Monitor"
    )
    
    print(f"Created job: {job_id}")
    
    # Get job details
    job = await job_service.get_job(job_id)
    if job:
        print(f"Job details:")
        print(f"  Name: {job.name}")
        print(f"  Type: {job.job_type}")
        print(f"  Schedule: {job.schedule}")
        print(f"  Status: {job.status}")
    
    # List all jobs
    jobs = await job_service.list_jobs(limit=10)
    print(f"\nTotal jobs: {len(jobs)}")


async def demo_account_creation_templates():
    """Demonstrate account creation templates."""
    print("\n=== Account Creation Templates Demo ===")
    
    from run_a_job.automation.account_creator import AccountCreator
    
    creator = AccountCreator()
    
    # Show supported platforms
    platforms = creator.get_supported_platforms()
    print(f"Supported platforms: {platforms}")
    
    # Show required fields for each platform
    for platform in platforms:
        fields = creator.get_required_fields(platform)
        print(f"{platform.title()} requires: {fields}")


async def demo_job_scheduling():
    """Demonstrate job scheduling capabilities."""
    print("\n=== Job Scheduling Demo ===")
    
    scheduler = JobScheduler()
    
    # Register a custom function
    async def check_website_example(url: str, selector: str = "body"):
        print(f"Checking {url} for selector {selector}")
        return {"status": "checked", "timestamp": "2024-01-01T00:00:00Z"}
    
    scheduler.register_function("check_website_example", check_website_example)
    
    # Add a scheduled job
    job_id = await scheduler.add_job(
        name="Example Monitor",
        function_name="check_website_example",
        parameters={"url": "https://example.com", "selector": ".content"},
        schedule="*/5 * * * *",  # Every 5 minutes
        job_type=JobType.WEBSITE_MONITORING
    )
    
    print(f"Scheduled job: {job_id}")
    
    # Start scheduler (commented out to avoid blocking)
    # await scheduler.start()
    print("Scheduler configured (start with scheduler.start())")


async def demo_captcha_handling():
    """Demonstrate CAPTCHA handling capabilities."""
    print("\n=== CAPTCHA Handling Demo ===")
    
    from run_a_job.automation.captcha import CaptchaSolver
    
    solver = CaptchaSolver()
    
    print("CAPTCHA solving features:")
    print("  - reCAPTCHA v2/v3 support")
    print("  - hCaptcha support")
    print("  - Cloudflare Turnstile support")
    print("  - Image-based CAPTCHA support")
    print("  - Integration with 2captcha service")
    print("  - Automatic detection and solving")


def demo_configuration():
    """Demonstrate configuration management."""
    print("\n=== Configuration Demo ===")
    
    from run_a_job.config.settings import settings
    
    print("Current configuration:")
    print(f"  Database URL: {settings.database_url}")
    print(f"  Browser headless: {settings.browser_headless}")
    print(f"  Max concurrent jobs: {settings.max_concurrent_jobs}")
    print(f"  Job timeout: {settings.job_timeout}s")
    print(f"  Log level: {settings.log_level}")
    
    print("\nEnvironment variables supported:")
    print("  BROWSER_HEADLESS, BROWSER_TIMEOUT")
    print("  TWOCAPTCHA_API_KEY, OPENAI_API_KEY")
    print("  DATABASE_URL, REDIS_URL")
    print("  MAX_CONCURRENT_JOBS, JOB_TIMEOUT")


async def main():
    """Run all demonstrations."""
    print("🚀 Run-a-Job Platform Demonstration")
    print("=" * 50)
    
    try:
        # Configuration demo (synchronous)
        demo_configuration()
        
        # Async demos
        await demo_workflow_translation()
        await demo_basic_browser_automation()
        await demo_job_creation()
        await demo_account_creation_templates()
        await demo_job_scheduling()
        await demo_captcha_handling()
        
        print("\n" + "=" * 50)
        print("✅ All demos completed successfully!")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Install Playwright browsers: playwright install")
        print("3. Start the scheduler: run-a-job start")
        print("4. Create jobs: run-a-job create-job 'your description'")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("This may be due to missing dependencies or configuration.")


if __name__ == "__main__":
    asyncio.run(main())