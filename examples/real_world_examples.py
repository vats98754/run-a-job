"""Real-world usage examples for the run-a-job platform."""

import asyncio
from run_a_job import JobService, BrowserAutomation
from run_a_job.automation.account_creator import AccountCreator


async def example_ticket_monitoring():
    """Example: Monitor concert ticket availability."""
    service = JobService()
    
    # Create a ticket monitoring job
    job_id = await service.create_job_from_description(
        "Check for Oasis concert tickets on Ticketmaster every 15 minutes",
        name="Oasis Ticket Monitor"
    )
    
    print(f"✅ Created ticket monitoring job: {job_id}")
    return job_id


async def example_visa_appointment_checker():
    """Example: Check visa appointment availability."""
    service = JobService()
    
    # Create visa appointment checker
    job_id = await service.create_job_from_description(
        "Monitor visa appointments on vfsglobal.com every morning at 8 AM",
        name="Visa Appointment Checker"
    )
    
    print(f"✅ Created visa monitoring job: {job_id}")
    return job_id


async def example_social_media_automation():
    """Example: Automated social media account creation."""
    creator = AccountCreator()
    
    # Show what platforms are supported
    platforms = creator.get_supported_platforms()
    print(f"📱 Supported platforms: {platforms}")
    
    # Example account data (use real data in practice)
    account_data = {
        "name": "John Doe",
        "email": "john.doe@example.com", 
        "username": "johndoe2024",
        "password": "SecurePassword123!"
    }
    
    # Create accounts (commented out to avoid actual creation)
    # for platform in ['twitter', 'reddit']:
    #     result = await creator.create_account(platform, account_data)
    #     print(f"Account creation result for {platform}: {result}")
    
    print("📝 Account creation templates ready for Twitter, Instagram, Reddit, GitHub")


async def example_price_monitoring():
    """Example: Monitor product prices."""
    service = JobService()
    
    # Create price monitoring job
    job_id = await service.create_job_from_description(
        "Scrape product prices from Amazon for iPhone 15 weekly on Sundays",
        name="iPhone Price Monitor"
    )
    
    print(f"💰 Created price monitoring job: {job_id}")
    return job_id


async def example_custom_browser_automation():
    """Example: Custom browser automation task."""
    
    # Define a custom automation function
    async def check_website_status(url: str, expected_text: str = None):
        """Check if a website is up and optionally contains specific text."""
        async with BrowserAutomation() as browser:
            try:
                await browser.navigate(url)
                
                # Take screenshot for evidence
                screenshot = await browser.take_screenshot()
                
                # Check for specific text if provided
                if expected_text:
                    page_text = await browser.execute_script("return document.body.innerText")
                    found = expected_text.lower() in page_text.lower()
                    return {
                        "status": "up",
                        "url": url,
                        "text_found": found,
                        "expected_text": expected_text,
                        "screenshot_size": len(screenshot)
                    }
                else:
                    return {
                        "status": "up", 
                        "url": url,
                        "screenshot_size": len(screenshot)
                    }
                    
            except Exception as e:
                return {
                    "status": "down",
                    "url": url, 
                    "error": str(e)
                }
    
    # Test the function (requires browser installation)
    try:
        result = await check_website_status("https://httpbin.org/html", "Herman Melville")
        print(f"🌐 Website check result: {result}")
    except Exception as e:
        print(f"⚠️  Browser automation requires: playwright install")
        print(f"   Error: {e}")


async def example_job_management():
    """Example: Managing jobs programmatically.""" 
    service = JobService()
    
    # Create multiple jobs
    jobs = []
    
    descriptions = [
        "Check GitHub for new releases daily",
        "Monitor cryptocurrency prices every hour", 
        "Backup website data weekly"
    ]
    
    for desc in descriptions:
        job_id = await service.create_job_from_description(desc)
        jobs.append(job_id)
        print(f"📋 Created job: {job_id[:8]}...")
    
    # List all jobs
    all_jobs = await service.list_jobs(limit=10)
    print(f"📊 Total jobs in system: {len(all_jobs)}")
    
    # Get statistics
    stats = await service.get_job_statistics()
    print(f"📈 Job statistics: {stats}")
    
    return jobs


async def main():
    """Run all examples."""
    print("🎯 Run-a-Job Real-World Examples")
    print("=" * 50)
    
    try:
        # Example use cases
        await example_ticket_monitoring()
        await example_visa_appointment_checker() 
        await example_social_media_automation()
        await example_price_monitoring()
        await example_custom_browser_automation()
        
        # Job management
        jobs = await example_job_management()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed!")
        print(f"💼 Created {len(jobs)} demo jobs")
        
        print("\n🚀 Ready to use:")
        print("1. run-a-job list-jobs")
        print("2. run-a-job create-job 'your task description'")
        print("3. run-a-job start")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())