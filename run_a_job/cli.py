"""Command line interface for run-a-job."""

import asyncio
import signal
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from run_a_job.config.logging import setup_logging, get_logger
from run_a_job.config.settings import settings
from run_a_job.scheduling.scheduler import JobScheduler
from run_a_job.scheduling.models import JobType, JobStatus
from run_a_job.automation.browser import BrowserAutomation
from run_a_job.services.job_service import JobService
from run_a_job.llm.workflow_translator import WorkflowTranslator


app = typer.Typer(
    name="run-a-job",
    help="Automated task orchestration platform",
    add_completion=False
)
console = Console()
logger = get_logger(__name__)


@app.command()
def start(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    workers: int = typer.Option(1, help="Number of worker processes"),
    scheduler_only: bool = typer.Option(False, help="Start only the scheduler without API"),
) -> None:
    """Start the job scheduler and optionally the API server."""
    setup_logging()
    
    if scheduler_only:
        asyncio.run(_start_scheduler_only())
    else:
        asyncio.run(_start_full_service(host, port))


@app.command()
def create_job(
    description: str = typer.Argument(..., help="Natural language description of the job"),
    name: Optional[str] = typer.Option(None, help="Job name (auto-generated if not provided)"),
    schedule: Optional[str] = typer.Option(None, help="Cron expression for scheduling"),
    job_type: str = typer.Option("browser_automation", help="Type of job to create"),
) -> None:
    """Create a new job from natural language description."""
    setup_logging()
    
    console.print(f"[bold green]Creating job from description:[/bold green] {description}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing...", total=None)
        
        try:
            result = asyncio.run(_create_job_from_description(
                description, name, schedule, job_type
            ))
            
            progress.update(task, completed=True)
            console.print(f"[bold green]✓[/bold green] Job created successfully!")
            console.print(f"[dim]Job ID:[/dim] {result['job_id']}")
            console.print(f"[dim]Name:[/dim] {result['name']}")
            if result.get('schedule'):
                console.print(f"[dim]Schedule:[/dim] {result['schedule']}")
                
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]✗[/bold red] Failed to create job: {e}")
            raise typer.Exit(1)


@app.command()
def list_jobs(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    job_type: Optional[str] = typer.Option(None, help="Filter by job type"),
    limit: int = typer.Option(20, help="Maximum number of jobs to show"),
) -> None:
    """List all jobs."""
    setup_logging()
    
    try:
        jobs = asyncio.run(_list_jobs(status, job_type, limit))
        
        if not jobs:
            console.print("[dim]No jobs found.[/dim]")
            return
            
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Name", style="bold")
        table.add_column("Type", width=15)
        table.add_column("Status", width=10)
        table.add_column("Schedule", width=15)
        table.add_column("Last Run", width=12)
        table.add_column("Runs", width=8, justify="right")
        
        for job in jobs:
            # Truncate ID for display
            short_id = job.id[:8]
            
            # Format status with color
            status_color = {
                JobStatus.PENDING: "yellow",
                JobStatus.RUNNING: "blue",
                JobStatus.COMPLETED: "green",
                JobStatus.FAILED: "red",
                JobStatus.CANCELLED: "dim",
                JobStatus.PAUSED: "orange1",
            }.get(job.status, "white")
            
            status_text = f"[{status_color}]{job.status}[/{status_color}]"
            
            # Format last run
            last_run = job.last_run.strftime("%m/%d %H:%M") if job.last_run else "-"
            
            table.add_row(
                short_id,
                job.name,
                job.job_type,
                status_text,
                job.schedule or "-",
                last_run,
                str(job.run_count),
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def show_job(job_id: str = typer.Argument(..., help="Job ID to show")) -> None:
    """Show detailed information about a job."""
    setup_logging()
    
    try:
        job = asyncio.run(_get_job_details(job_id))
        
        if not job:
            console.print(f"[bold red]Job {job_id} not found.[/bold red]")
            raise typer.Exit(1)
            
        # Display job details
        console.print(f"[bold]Job Details[/bold]")
        console.print(f"[dim]ID:[/dim] {job.id}")
        console.print(f"[dim]Name:[/dim] {job.name}")
        console.print(f"[dim]Description:[/dim] {job.description or 'N/A'}")
        console.print(f"[dim]Type:[/dim] {job.job_type}")
        console.print(f"[dim]Status:[/dim] {job.status}")
        console.print(f"[dim]Function:[/dim] {job.function_name}")
        
        if job.schedule:
            console.print(f"[dim]Schedule:[/dim] {job.schedule}")
            console.print(f"[dim]Next Run:[/dim] {job.next_run or 'N/A'}")
            
        console.print(f"[dim]Created:[/dim] {job.created_at}")
        console.print(f"[dim]Last Run:[/dim] {job.last_run or 'Never'}")
        
        # Statistics
        console.print(f"\n[bold]Statistics[/bold]")
        console.print(f"[dim]Total Runs:[/dim] {job.run_count}")
        console.print(f"[dim]Successful:[/dim] {job.success_count}")
        console.print(f"[dim]Failed:[/dim] {job.failure_count}")
        
        # Parameters
        if job.parameters:
            console.print(f"\n[bold]Parameters[/bold]")
            for key, value in job.parameters.items():
                console.print(f"[dim]{key}:[/dim] {value}")
                
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def run_job(job_id: str = typer.Argument(..., help="Job ID to run")) -> None:
    """Run a job immediately."""
    setup_logging()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running job...", total=None)
        
        try:
            result = asyncio.run(_run_job_now(job_id))
            progress.update(task, completed=True)
            
            console.print(f"[bold green]✓[/bold green] Job executed successfully!")
            console.print(f"[dim]Run ID:[/dim] {result}")
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]✗[/bold red] Job execution failed: {e}")
            raise typer.Exit(1)


@app.command()
def stop_job(job_id: str = typer.Argument(..., help="Job ID to stop")) -> None:
    """Stop/pause a job."""
    setup_logging()
    
    try:
        success = asyncio.run(_pause_job(job_id))
        
        if success:
            console.print(f"[bold green]✓[/bold green] Job {job_id} paused successfully")
        else:
            console.print(f"[bold red]✗[/bold red] Failed to pause job {job_id}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def resume_job(job_id: str = typer.Argument(..., help="Job ID to resume")) -> None:
    """Resume a paused job."""
    setup_logging()
    
    try:
        success = asyncio.run(_resume_job(job_id))
        
        if success:
            console.print(f"[bold green]✓[/bold green] Job {job_id} resumed successfully")
        else:
            console.print(f"[bold red]✗[/bold red] Failed to resume job {job_id}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def delete_job(
    job_id: str = typer.Argument(..., help="Job ID to delete"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
) -> None:
    """Delete a job."""
    setup_logging()
    
    if not confirm:
        if not typer.confirm(f"Are you sure you want to delete job {job_id}?"):
            console.print("Cancelled.")
            return
            
    try:
        success = asyncio.run(_delete_job(job_id))
        
        if success:
            console.print(f"[bold green]✓[/bold green] Job {job_id} deleted successfully")
        else:
            console.print(f"[bold red]✗[/bold red] Job {job_id} not found")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
) -> None:
    """Start the API server."""
    setup_logging()
    
    console.print(f"[bold green]Starting API server on {host}:{port}[/bold green]")
    
    try:
        import uvicorn
        from run_a_job.api.main import app as api_app
        
        uvicorn.run(
            api_app,
            host=host,
            port=port,
            reload=reload,
            log_level=settings.log_level.lower()
        )
        
    except ImportError:
        console.print("[bold red]Error:[/bold red] uvicorn not installed")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error starting server:[/bold red] {e}")
        raise typer.Exit(1)


# Async helper functions

async def _start_scheduler_only() -> None:
    """Start only the job scheduler."""
    scheduler = JobScheduler()
    
    # Register signal handlers
    def signal_handler(signum, frame):
        console.print("\n[yellow]Shutting down scheduler...[/yellow]")
        asyncio.create_task(scheduler.stop())
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register built-in job functions
    await _register_job_functions(scheduler)
    
    try:
        await scheduler.start()
        console.print("[bold green]Job scheduler started[/bold green]")
        console.print("Press Ctrl+C to stop")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        await scheduler.stop()
        console.print("[yellow]Scheduler stopped[/yellow]")


async def _start_full_service(host: str, port: int) -> None:
    """Start both scheduler and API server."""
    # This would start both the scheduler and API in the background
    console.print(f"[bold green]Starting full service on {host}:{port}[/bold green]")
    console.print("[dim]Use 'run-a-job serve' for API-only mode[/dim]")


async def _create_job_from_description(
    description: str,
    name: Optional[str],
    schedule: Optional[str],
    job_type: str
) -> dict:
    """Create a job from natural language description."""
    translator = WorkflowTranslator()
    job_service = JobService()
    
    # Translate description to workflow
    workflow = await translator.translate(description)
    
    # Create job
    job_id = await job_service.create_job_from_workflow(
        workflow,
        name=name,
        schedule=schedule
    )
    
    return {
        "job_id": job_id,
        "name": workflow.get("name", name),
        "schedule": schedule,
        "workflow": workflow
    }


async def _list_jobs(status: Optional[str], job_type: Optional[str], limit: int):
    """List jobs with filtering."""
    job_service = JobService()
    
    status_enum = JobStatus(status) if status else None
    type_enum = JobType(job_type) if job_type else None
    
    return await job_service.list_jobs(
        status=status_enum,
        job_type=type_enum,
        limit=limit
    )


async def _get_job_details(job_id: str):
    """Get detailed job information."""
    job_service = JobService()
    return await job_service.get_job(job_id)


async def _run_job_now(job_id: str) -> str:
    """Run a job immediately."""
    job_service = JobService()
    return await job_service.run_job_now(job_id)


async def _pause_job(job_id: str) -> bool:
    """Pause a job."""
    job_service = JobService()
    return await job_service.pause_job(job_id)


async def _resume_job(job_id: str) -> bool:
    """Resume a job."""
    job_service = JobService()
    return await job_service.resume_job(job_id)


async def _delete_job(job_id: str) -> bool:
    """Delete a job."""
    job_service = JobService()
    return await job_service.delete_job(job_id)


async def _register_job_functions(scheduler: JobScheduler) -> None:
    """Register built-in job functions."""
    from run_a_job.automation.browser import BrowserAutomation
    from run_a_job.automation.account_creator import AccountCreator
    
    # Register browser automation functions
    async def check_website(url: str, selector: str = None, text: str = None):
        """Check if a website contains specific content."""
        async with BrowserAutomation() as browser:
            await browser.navigate(url)
            
            if selector:
                await browser.wait_for_element(selector)
                if text:
                    element_text = await browser.get_text(selector)
                    return {"found": text.lower() in element_text.lower(), "text": element_text}
                else:
                    return {"found": True}
            
            return {"status": "checked", "url": url}
    
    scheduler.register_function("check_website", check_website)
    
    # Register more functions as needed
    # ...


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()