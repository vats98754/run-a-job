# Run-a-Job: Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/vats98754/run-a-job.git
cd run-a-job

# Install the package
pip install -e .

# Install browsers for automation
playwright install
```

## Basic Usage

### 1. Command Line Interface

```bash
# Create a job from natural language
run-a-job create-job "Check for Oasis concert tickets every hour"

# List all jobs
run-a-job list-jobs

# Run a job immediately
run-a-job run-job <job-id>

# Start the scheduler
run-a-job start
```

### 2. Python API

```python
import asyncio
from run_a_job import JobService, BrowserAutomation

async def main():
    # Create job service
    service = JobService()
    
    # Create a job
    job_id = await service.create_job_from_description(
        "Monitor visa appointments daily at 9 AM"
    )
    
    # Browser automation
    async with BrowserAutomation() as browser:
        await browser.navigate("https://example.com")
        screenshot = await browser.take_screenshot()

asyncio.run(main())
```

### 3. Natural Language Examples

The platform can translate natural language into automation workflows:

- ✅ "Check for Oasis concert tickets every hour"
- ✅ "Create 5 Twitter accounts daily at 9 AM"  
- ✅ "Monitor visa appointments on vfsglobal.com every morning"
- ✅ "Scrape product prices from Amazon weekly"

## Configuration

Create a `.env` file:

```env
# Browser settings
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000

# CAPTCHA services (optional)
TWOCAPTCHA_API_KEY=your_api_key

# LLM integration (optional) 
OPENAI_API_KEY=your_openai_key

# Database
DATABASE_URL=sqlite+aiosqlite:///jobs.db

# Job limits
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT=3600
```

## Key Features

### ✅ Browser Automation
- Playwright-powered web automation
- Anti-detection features
- Human-like behavior simulation
- Screenshot and data extraction

### ✅ CAPTCHA Bypassing
- reCAPTCHA v2/v3 solving
- Cloudflare Turnstile bypass
- hCaptcha support
- Image CAPTCHA recognition
- 2captcha service integration

### ✅ Account Creation
- Pre-built templates for major platforms:
  - Twitter/X
  - Instagram
  - Reddit
  - GitHub
- Automated form filling
- Email verification handling

### ✅ Job Scheduling
- Cron expression support
- APScheduler integration
- Persistent job storage
- Retry mechanisms
- Concurrent execution limits

### ✅ LLM Integration
- Natural language to workflow translation
- OpenAI and Anthropic support
- Intelligent parameter extraction
- Schedule parsing

### ✅ Cloud Ready
- Background process support
- API server included
- Database persistence
- Redis integration for scaling

## Architecture

```
run_a_job/
├── api/          # REST API layer
├── automation/   # Browser & account automation
├── config/       # Configuration management
├── llm/          # LLM workflow translation
├── repositories/ # Data persistence layer
├── scheduling/   # Job scheduling system
├── services/     # Business logic layer
└── utils/        # Utility functions
```

## Examples

See the `examples/` directory for:
- `simple_demo.py` - Core features demonstration
- `demo.py` - Comprehensive feature showcase

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black run_a_job tests
isort run_a_job tests

# Type checking
mypy run_a_job
```

## Support

This platform is designed for legitimate automation purposes. Please:
- Respect website terms of service
- Follow rate limits and robots.txt
- Use responsibly and ethically

For questions and support, see the GitHub repository.