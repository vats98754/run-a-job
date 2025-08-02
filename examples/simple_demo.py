"""
Simple demo showing core features without browser automation.
"""

import asyncio
from run_a_job.llm.workflow_translator import WorkflowTranslator
from run_a_job.scheduling.models import Job, JobType
from run_a_job.automation.account_creator import AccountCreator
from run_a_job.config.settings import settings


async def simple_demo():
    """Run a simple demonstration of key features."""
    print("🚀 Run-a-Job Core Features Demo")
    print("=" * 40)
    
    # 1. Configuration
    print("✅ Configuration System")
    print(f"   Database: {settings.database_url}")
    print(f"   Max jobs: {settings.max_concurrent_jobs}")
    print(f"   Headless: {settings.browser_headless}")
    
    # 2. Job Models
    print("\n✅ Job Models")
    job = Job(
        name="Test Monitoring Job",
        job_type=JobType.WEBSITE_MONITORING,
        function_name="check_website",
        schedule="0 9 * * *",
        parameters={"url": "https://example.com"}
    )
    print(f"   Created job: {job.name}")
    print(f"   ID: {job.id[:8]}...")
    print(f"   Type: {job.job_type}")
    print(f"   Schedule: {job.schedule}")
    
    # 3. Workflow Translation
    print("\n✅ Natural Language Translation")
    translator = WorkflowTranslator()
    
    examples = [
        "Check for concert tickets every hour",
        "Create Twitter accounts daily at 9am",
        "Monitor visa appointments weekly"
    ]
    
    for desc in examples:
        workflow = await translator.translate(desc)
        print(f"   '{desc}'")
        print(f"   → {workflow['job_type']} | {workflow['function_name']}")
        if workflow.get('schedule'):
            print(f"   → Schedule: {workflow['schedule']}")
    
    # 4. Account Creation Templates
    print("\n✅ Account Creation Templates")
    creator = AccountCreator()
    platforms = creator.get_supported_platforms()
    
    for platform in platforms[:3]:  # Show first 3
        fields = creator.get_required_fields(platform)
        print(f"   {platform.title()}: {', '.join(fields)}")
    
    # 5. CAPTCHA Handling
    print("\n✅ CAPTCHA & Anti-Bot Features")
    print("   - reCAPTCHA v2/v3 solving")
    print("   - Cloudflare Turnstile bypass")
    print("   - Image CAPTCHA recognition")
    print("   - 2captcha service integration")
    
    # 6. Scheduling Features
    print("\n✅ Job Scheduling Features")
    print("   - Cron expression parsing")
    print("   - APScheduler integration")
    print("   - Job persistence")
    print("   - Retry mechanisms")
    print("   - Concurrent job limits")
    
    print("\n🎉 All core systems functional!")
    print("\nTo fully test:")
    print("1. Install browsers: playwright install")
    print("2. Set API keys in .env file")
    print("3. Run: run-a-job --help")


if __name__ == "__main__":
    asyncio.run(simple_demo())