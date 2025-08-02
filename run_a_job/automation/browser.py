"""Core browser automation using Playwright."""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from run_a_job.config.settings import settings
from run_a_job.config.logging import get_logger
from run_a_job.automation.captcha import CaptchaSolver


logger = get_logger(__name__)


class BrowserAutomation:
    """High-level browser automation with anti-detection features."""
    
    def __init__(
        self,
        headless: bool = None,
        timeout: int = None,
        viewport_width: int = None,
        viewport_height: int = None,
        user_agent: str = None
    ):
        """Initialize browser automation.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in milliseconds
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            user_agent: Custom user agent string
        """
        self.headless = headless if headless is not None else settings.browser_headless
        self.timeout = timeout if timeout is not None else settings.browser_timeout
        self.viewport_width = viewport_width or settings.browser_viewport_width
        self.viewport_height = viewport_height or settings.browser_viewport_height
        self.user_agent = user_agent or settings.browser_user_agent
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.captcha_solver = CaptchaSolver()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def start(self) -> None:
        """Start the browser instance."""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with anti-detection features
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-web-security",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={"width": self.viewport_width, "height": self.viewport_height},
                user_agent=self.user_agent or await self._get_random_user_agent(),
                locale="en-US",
                timezone_id="America/New_York",
                permissions=["geolocation", "notifications"],
                geolocation={"latitude": 40.7128, "longitude": -74.0060},  # New York
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
            
            # Add stealth scripts
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.timeout)
            
            logger.info("Browser automation started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            await self.close()
            raise
            
    async def close(self) -> None:
        """Close the browser instance."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            logger.info("Browser automation closed")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            
    async def navigate(self, url: str, wait_for: str = "networkidle") -> None:
        """Navigate to a URL with human-like behavior.
        
        Args:
            url: URL to navigate to
            wait_for: Wait condition ('load', 'domcontentloaded', 'networkidle')
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
            
        try:
            # Add random delay to simulate human behavior
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_for)
            
            # Random delay after page load
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
        except PlaywrightTimeoutError:
            logger.error(f"Timeout navigating to {url}")
            raise
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
            
    async def click(self, selector: str, human_like: bool = True) -> None:
        """Click an element with optional human-like behavior.
        
        Args:
            selector: CSS selector for the element
            human_like: Whether to add human-like delays and movement
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        try:
            if human_like:
                # Scroll element into view
                await self.page.locator(selector).scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.2, 0.8))
                
                # Hover before clicking
                await self.page.locator(selector).hover()
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
            await self.page.locator(selector).click()
            
            if human_like:
                await asyncio.sleep(random.uniform(0.3, 1.0))
                
        except Exception as e:
            logger.error(f"Error clicking {selector}: {e}")
            raise
            
    async def type_text(self, selector: str, text: str, human_like: bool = True) -> None:
        """Type text into an input field.
        
        Args:
            selector: CSS selector for the input element
            text: Text to type
            human_like: Whether to add human-like typing delays
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        try:
            await self.page.locator(selector).click()
            
            if human_like:
                # Clear existing text
                await self.page.locator(selector).press("Control+a")
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
                # Type with random delays between characters
                for char in text:
                    await self.page.locator(selector).type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
            else:
                await self.page.locator(selector).fill(text)
                
        except Exception as e:
            logger.error(f"Error typing into {selector}: {e}")
            raise
            
    async def wait_for_element(
        self, 
        selector: str, 
        state: str = "visible",
        timeout: int = None
    ) -> None:
        """Wait for an element to reach a specific state.
        
        Args:
            selector: CSS selector for the element
            state: State to wait for ('visible', 'hidden', 'attached', 'detached')
            timeout: Timeout in milliseconds (uses default if None)
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        timeout = timeout or self.timeout
        
        try:
            await self.page.locator(selector).wait_for(state=state, timeout=timeout)
        except PlaywrightTimeoutError:
            logger.error(f"Timeout waiting for {selector} to be {state}")
            raise
            
    async def get_text(self, selector: str) -> str:
        """Get text content of an element.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            Text content of the element
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        try:
            return await self.page.locator(selector).text_content() or ""
        except Exception as e:
            logger.error(f"Error getting text from {selector}: {e}")
            raise
            
    async def take_screenshot(self, path: Optional[str] = None) -> bytes:
        """Take a screenshot of the current page.
        
        Args:
            path: Optional file path to save the screenshot
            
        Returns:
            Screenshot bytes
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        try:
            screenshot = await self.page.screenshot(
                path=path,
                full_page=True,
                type="png"
            )
            logger.info(f"Screenshot taken{f' and saved to {path}' if path else ''}")
            return screenshot
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            raise
            
    async def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Result of the JavaScript execution
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        try:
            return await self.page.evaluate(script, *args)
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            raise
            
    async def solve_captcha(self, selector: str = None) -> bool:
        """Attempt to solve CAPTCHA on the current page.
        
        Args:
            selector: Optional selector for the CAPTCHA element
            
        Returns:
            True if CAPTCHA was solved, False otherwise
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        try:
            return await self.captcha_solver.solve(self.page, selector)
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            return False
            
    async def bypass_cloudflare(self, max_attempts: int = 5) -> bool:
        """Attempt to bypass Cloudflare protection.
        
        Args:
            max_attempts: Maximum number of attempts
            
        Returns:
            True if bypass was successful, False otherwise
        """
        if not self.page:
            raise RuntimeError("Browser not started")
            
        for attempt in range(max_attempts):
            try:
                # Check if we're on a Cloudflare challenge page
                if await self.page.locator('[data-ray]').count() > 0:
                    logger.info(f"Cloudflare challenge detected (attempt {attempt + 1})")
                    
                    # Wait for challenge to complete
                    await self.page.wait_for_load_state("networkidle", timeout=30000)
                    
                    # Look for success indicators
                    await asyncio.sleep(5)
                    
                    # Check if challenge was passed
                    if await self.page.locator('[data-ray]').count() == 0:
                        logger.info("Cloudflare challenge bypassed successfully")
                        return True
                        
                else:
                    # No challenge detected
                    return True
                    
            except Exception as e:
                logger.warning(f"Cloudflare bypass attempt {attempt + 1} failed: {e}")
                
            # Wait before retry
            if attempt < max_attempts - 1:
                await asyncio.sleep(random.uniform(2, 5))
                
        logger.error("Failed to bypass Cloudflare after all attempts")
        return False
        
    async def _get_random_user_agent(self) -> str:
        """Get a random realistic user agent string."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        return random.choice(user_agents)