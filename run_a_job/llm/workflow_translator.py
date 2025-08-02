"""LLM-powered workflow translation from natural language."""

import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from run_a_job.config.settings import settings
from run_a_job.config.logging import get_logger
from run_a_job.scheduling.models import JobType


logger = get_logger(__name__)


class WorkflowTranslator:
    """Translate natural language descriptions into automation workflows."""
    
    def __init__(self):
        """Initialize workflow translator."""
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize clients if API keys are available
        if settings.openai_api_key:
            try:
                import openai
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.warning("OpenAI client not available")
                
        if settings.anthropic_api_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            except ImportError:
                logger.warning("Anthropic client not available")
                
    async def translate(self, description: str) -> Dict[str, Any]:
        """Translate natural language description to workflow.
        
        Args:
            description: Natural language description of the task
            
        Returns:
            Workflow dictionary with job configuration
        """
        logger.info(f"Translating description: {description}")
        
        # Try LLM translation first
        if self.openai_client or self.anthropic_client:
            try:
                return await self._llm_translate(description)
            except Exception as e:
                logger.warning(f"LLM translation failed: {e}")
                
        # Fallback to rule-based translation
        return await self._rule_based_translate(description)
        
    async def _llm_translate(self, description: str) -> Dict[str, Any]:
        """Use LLM to translate description to workflow."""
        prompt = self._build_translation_prompt(description)
        
        # Try OpenAI first
        if self.openai_client:
            try:
                response = await self.openai_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                content = response.choices[0].message.content
                return self._parse_llm_response(content)
                
            except Exception as e:
                logger.error(f"OpenAI translation failed: {e}")
                
        # Try Anthropic as fallback
        if self.anthropic_client:
            try:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": f"{self._get_system_prompt()}\n\n{prompt}"}
                    ]
                )
                
                content = response.content[0].text
                return self._parse_llm_response(content)
                
            except Exception as e:
                logger.error(f"Anthropic translation failed: {e}")
                
        raise Exception("No LLM client available")
        
    async def _rule_based_translate(self, description: str) -> Dict[str, Any]:
        """Rule-based translation as fallback."""
        description_lower = description.lower()
        
        # Detect job type
        job_type = self._detect_job_type(description_lower)
        
        # Extract schedule
        schedule = self._extract_schedule(description_lower)
        
        # Extract URLs
        urls = self._extract_urls(description)
        
        # Extract key actions
        actions = self._extract_actions(description_lower)
        
        # Generate job name
        name = self._generate_job_name(description)
        
        # Build workflow
        workflow = {
            "name": name,
            "description": description,
            "job_type": job_type,
            "function_name": self._determine_function(job_type, actions),
            "parameters": self._build_parameters(job_type, urls, actions, description),
            "schedule": schedule,
            "tags": self._extract_tags(description_lower)
        }
        
        logger.info(f"Generated workflow: {workflow}")
        return workflow
        
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM translation."""
        return """You are an expert at translating natural language task descriptions into automation workflows.

Your job is to analyze a user's description and create a structured workflow configuration.

Return your response as a JSON object with these fields:
- name: Short descriptive name for the job
- description: The original description
- job_type: One of: browser_automation, account_creation, website_monitoring, data_scraping, custom_script
- function_name: The function to call (e.g., check_website, create_accounts, scrape_data)
- parameters: Object with function parameters
- schedule: Cron expression if scheduling is mentioned (e.g., "0 9 * * *" for daily at 9am)
- tags: Array of relevant tags

Example output:
{
  "name": "Check Concert Tickets",
  "description": "Check for Oasis concert tickets every hour",
  "job_type": "website_monitoring",
  "function_name": "check_website",
  "parameters": {
    "url": "https://ticketmaster.com/oasis",
    "selector": ".ticket-available",
    "notify_on_found": true
  },
  "schedule": "0 * * * *",
  "tags": ["tickets", "monitoring", "oasis"]
}

Be precise and practical in your translations."""
        
    def _build_translation_prompt(self, description: str) -> str:
        """Build prompt for LLM translation."""
        return f"""Please translate this task description into a structured workflow:

"{description}"

Analyze what the user wants to accomplish and create an appropriate automation workflow configuration."""
        
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON workflow."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                workflow = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["name", "job_type", "function_name"]
                for field in required_fields:
                    if field not in workflow:
                        raise ValueError(f"Missing required field: {field}")
                        
                # Set defaults
                workflow.setdefault("parameters", {})
                workflow.setdefault("tags", [])
                
                return workflow
            else:
                raise ValueError("No JSON found in LLM response")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            raise ValueError("Invalid JSON in LLM response")
            
    def _detect_job_type(self, description: str) -> str:
        """Detect job type from description."""
        if any(word in description for word in ["account", "signup", "register", "create account"]):
            return JobType.ACCOUNT_CREATION
        elif any(word in description for word in ["check", "monitor", "watch", "alert", "notify"]):
            return JobType.WEBSITE_MONITORING
        elif any(word in description for word in ["scrape", "extract", "collect", "data", "download"]):
            return JobType.DATA_SCRAPING
        elif any(word in description for word in ["click", "fill", "submit", "browse", "navigate"]):
            return JobType.BROWSER_AUTOMATION
        else:
            return JobType.CUSTOM_SCRIPT
            
    def _extract_schedule(self, description: str) -> Optional[str]:
        """Extract schedule from description."""
        # Daily patterns
        if "daily" in description or "every day" in description:
            if "morning" in description:
                return "0 9 * * *"  # 9 AM daily
            elif "evening" in description:
                return "0 18 * * *"  # 6 PM daily
            else:
                return "0 0 * * *"  # Midnight daily
                
        # Hourly patterns
        if "hourly" in description or "every hour" in description:
            return "0 * * * *"
            
        # Weekly patterns
        if "weekly" in description or "every week" in description:
            return "0 9 * * 1"  # Monday 9 AM
            
        # Specific times
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', description)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
                
            return f"{minute} {hour} * * *"
            
        # Interval patterns
        interval_match = re.search(r'every (\d+) (minute|hour|day)', description)
        if interval_match:
            interval = int(interval_match.group(1))
            unit = interval_match.group(2)
            
            if unit == "minute":
                return f"*/{interval} * * * *"
            elif unit == "hour":
                return f"0 */{interval} * * *"
            elif unit == "day":
                return f"0 0 */{interval} * *"
                
        return None
        
    def _extract_urls(self, description: str) -> List[str]:
        """Extract URLs from description."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, description)
        
    def _extract_actions(self, description: str) -> List[str]:
        """Extract action verbs from description."""
        actions = []
        action_words = [
            "check", "monitor", "watch", "click", "fill", "submit",
            "scrape", "extract", "download", "upload", "search",
            "login", "logout", "navigate", "wait", "verify"
        ]
        
        for word in action_words:
            if word in description:
                actions.append(word)
                
        return actions
        
    def _generate_job_name(self, description: str) -> str:
        """Generate a job name from description."""
        # Take first 50 characters and clean up
        name = description[:50].strip()
        if len(description) > 50:
            name += "..."
            
        # Capitalize first letter
        if name:
            name = name[0].upper() + name[1:]
            
        return name or "Automated Job"
        
    def _determine_function(self, job_type: str, actions: List[str]) -> str:
        """Determine function name based on job type and actions."""
        if job_type == JobType.WEBSITE_MONITORING:
            return "check_website"
        elif job_type == JobType.ACCOUNT_CREATION:
            return "create_accounts"
        elif job_type == JobType.DATA_SCRAPING:
            return "scrape_data"
        elif job_type == JobType.BROWSER_AUTOMATION:
            if "login" in actions:
                return "browser_login"
            elif "click" in actions:
                return "browser_click"
            elif "fill" in actions:
                return "browser_fill_form"
            else:
                return "browser_automation"
        else:
            return "custom_script"
            
    def _build_parameters(
        self,
        job_type: str,
        urls: List[str],
        actions: List[str],
        description: str
    ) -> Dict[str, Any]:
        """Build parameters based on job type and extracted information."""
        params = {}
        
        if urls:
            params["url"] = urls[0]  # Use first URL found
            
        if job_type == JobType.WEBSITE_MONITORING:
            params.setdefault("selector", ".content")
            params["notify_on_change"] = True
            
        elif job_type == JobType.ACCOUNT_CREATION:
            params["platform"] = self._detect_platform(description)
            params["account_data"] = {}
            
        elif job_type == JobType.DATA_SCRAPING:
            params.setdefault("output_format", "json")
            params["selectors"] = {}
            
        # Add common browser options
        if job_type in [JobType.BROWSER_AUTOMATION, JobType.WEBSITE_MONITORING, JobType.DATA_SCRAPING]:
            params["headless"] = True
            params["timeout"] = 30000
            
        return params
        
    def _detect_platform(self, description: str) -> str:
        """Detect platform name from description."""
        platforms = ["twitter", "instagram", "facebook", "linkedin", "github", "reddit"]
        description_lower = description.lower()
        
        for platform in platforms:
            if platform in description_lower:
                return platform
                
        return "unknown"
        
    def _extract_tags(self, description: str) -> List[str]:
        """Extract relevant tags from description."""
        tags = []
        
        # Action-based tags
        if "monitor" in description or "check" in description:
            tags.append("monitoring")
        if "scrape" in description or "extract" in description:
            tags.append("scraping")
        if "account" in description or "signup" in description:
            tags.append("accounts")
            
        # Platform tags
        platforms = ["twitter", "instagram", "facebook", "linkedin", "github", "reddit"]
        for platform in platforms:
            if platform in description:
                tags.append(platform)
                
        # Frequency tags
        if "daily" in description:
            tags.append("daily")
        elif "hourly" in description:
            tags.append("hourly")
        elif "weekly" in description:
            tags.append("weekly")
            
        return list(set(tags))  # Remove duplicates