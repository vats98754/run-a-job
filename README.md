# Run a Job - Automated Task Orchestration Platform

Sometimes you want to run a job at a regular or irregular interval but it's hard for the layperson to do. This platform provides an easy-to-use solution for automating browser tasks, scheduling jobs, and managing background processes.

## Features

### Core Capabilities
- **Browser Automation**: Powered by Playwright for reliable web automation
- **CAPTCHA & Turnstile Bypassing**: Intelligent bypassing of common anti-bot measures
- **Account Creation Automation**: Automated account creation for various social media platforms
- **Job Scheduling**: Flexible cron job scheduling with APScheduler
- **Background Processing**: Cloud-ready background process management
- **LLM Integration**: Natural language to automation workflow translation
- **Robust Execution**: Deterministic browser automation with retry mechanisms
- **High Performance**: Optimized for quick response times

### Use Cases
- Monitor websites for changes (e.g., ticket availability, visa appointments)
- Automate social media account creation and management
- Schedule regular data collection tasks
- Perform routine web-based administrative tasks
- Translate natural language requests into automated workflows

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Command Line Interface
```bash
# Start the job scheduler
run-a-job start

# Create a new job from natural language
run-a-job create-job "Check for Oasis concert tickets every hour"

# List active jobs
run-a-job list-jobs

# Stop a specific job
run-a-job stop-job <job-id>
```

### Python API
```python
from run_a_job import JobScheduler, BrowserAutomation

# Create a browser automation instance
browser = BrowserAutomation()

# Schedule a job
scheduler = JobScheduler()
scheduler.add_job(
    func=browser.check_website,
    args=["https://example.com"],
    trigger="cron",
    hour=9,
    minute=0
)
```

### REST API
Start the API server:
```bash
run-a-job serve --port 8000
```

Create jobs via HTTP:
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"description": "Check visa appointments daily", "schedule": "0 9 * * *"}'
```

## Configuration

Create a `.env` file or set environment variables:

```env
# Browser settings
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000

# CAPTCHA service (optional)
TWOCAPTCHA_API_KEY=your_api_key

# LLM integration (optional)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
DATABASE_URL=sqlite:///jobs.db

# Redis (for background tasks)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

## Architecture

The project follows a layered architecture:

```
run_a_job/
├── api/                 # REST API layer
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── automation/          # Browser automation components
├── scheduling/          # Job scheduling components
├── llm/                # LLM integration
├── config/             # Configuration management
└── utils/              # Utility functions
```

## Development

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/your-org/run-a-job.git
cd run-a-job

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Install Playwright browsers
playwright install
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=run_a_job

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Code Quality
```bash
# Format code
black run_a_job tests
isort run_a_job tests

# Lint code
flake8 run_a_job tests
mypy run_a_job

# Security check
bandit -r run_a_job
```

## Deployment

### Docker
```bash
docker build -t run-a-job .
docker run -d -p 8000:8000 run-a-job
```

### Cloud Platforms (Render, Railway, etc.)
The application is designed to work on cloud platforms that support background processes. See the deployment guide for platform-specific instructions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Notice

This tool is designed for legitimate automation purposes. Please ensure you comply with the terms of service of any websites you interact with and respect rate limits and robots.txt files.
