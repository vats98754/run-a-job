"""CAPTCHA and anti-bot measure bypassing."""

import asyncio
import base64
import io
from typing import Optional, Dict, Any

import httpx
from PIL import Image
from playwright.async_api import Page

from run_a_job.config.settings import settings
from run_a_job.config.logging import get_logger


logger = get_logger(__name__)


class CaptchaSolver:
    """CAPTCHA solving using various services and techniques."""
    
    def __init__(self):
        """Initialize CAPTCHA solver."""
        self.twocaptcha_key = settings.twocaptcha_api_key
        self.anticaptcha_key = settings.anticaptcha_api_key
        
    async def solve(self, page: Page, selector: str = None) -> bool:
        """Attempt to solve CAPTCHA on the page.
        
        Args:
            page: Playwright page instance
            selector: Optional selector for the CAPTCHA element
            
        Returns:
            True if CAPTCHA was solved, False otherwise
        """
        try:
            # Try to detect and solve different types of CAPTCHAs
            if await self._detect_recaptcha(page):
                return await self._solve_recaptcha(page)
            elif await self._detect_hcaptcha(page):
                return await self._solve_hcaptcha(page)
            elif await self._detect_turnstile(page):
                return await self._solve_turnstile(page)
            elif await self._detect_image_captcha(page):
                return await self._solve_image_captcha(page, selector)
            else:
                logger.info("No CAPTCHA detected")
                return True
                
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            return False
            
    async def _detect_recaptcha(self, page: Page) -> bool:
        """Detect reCAPTCHA on the page."""
        try:
            # Check for reCAPTCHA elements
            selectors = [
                ".g-recaptcha",
                "[data-sitekey]",
                "#recaptcha",
                "iframe[src*='recaptcha']"
            ]
            
            for selector in selectors:
                if await page.locator(selector).count() > 0:
                    logger.info("reCAPTCHA detected")
                    return True
                    
            return False
        except Exception:
            return False
            
    async def _detect_hcaptcha(self, page: Page) -> bool:
        """Detect hCaptcha on the page."""
        try:
            selectors = [
                ".h-captcha",
                "[data-sitekey][data-theme]",
                "iframe[src*='hcaptcha']"
            ]
            
            for selector in selectors:
                if await page.locator(selector).count() > 0:
                    logger.info("hCaptcha detected")
                    return True
                    
            return False
        except Exception:
            return False
            
    async def _detect_turnstile(self, page: Page) -> bool:
        """Detect Cloudflare Turnstile on the page."""
        try:
            selectors = [
                ".cf-turnstile",
                "[data-sitekey][data-theme][data-callback]",
                "iframe[src*='turnstile']"
            ]
            
            for selector in selectors:
                if await page.locator(selector).count() > 0:
                    logger.info("Cloudflare Turnstile detected")
                    return True
                    
            return False
        except Exception:
            return False
            
    async def _detect_image_captcha(self, page: Page) -> bool:
        """Detect image-based CAPTCHA on the page."""
        try:
            selectors = [
                "img[src*='captcha']",
                ".captcha-image",
                "#captcha_image",
                "canvas[id*='captcha']"
            ]
            
            for selector in selectors:
                if await page.locator(selector).count() > 0:
                    logger.info("Image CAPTCHA detected")
                    return True
                    
            return False
        except Exception:
            return False
            
    async def _solve_recaptcha(self, page: Page) -> bool:
        """Solve reCAPTCHA using 2captcha service."""
        if not self.twocaptcha_key:
            logger.warning("No 2captcha API key configured")
            return False
            
        try:
            # Get site key
            site_key = await page.evaluate("""
                () => {
                    const element = document.querySelector('[data-sitekey]');
                    return element ? element.getAttribute('data-sitekey') : null;
                }
            """)
            
            if not site_key:
                logger.error("Could not find reCAPTCHA site key")
                return False
                
            # Submit to 2captcha
            current_url = page.url
            captcha_id = await self._submit_recaptcha_to_2captcha(site_key, current_url)
            
            if not captcha_id:
                return False
                
            # Get solution
            solution = await self._get_2captcha_solution(captcha_id)
            
            if not solution:
                return False
                
            # Submit solution
            await page.evaluate(f"""
                () => {{
                    if (window.grecaptcha) {{
                        window.grecaptcha.getResponse = () => '{solution}';
                        const callback = window.grecaptcha.getResponse();
                        if (callback) {{
                            callback('{solution}');
                        }}
                    }}
                }}
            """)
            
            logger.info("reCAPTCHA solution submitted")
            return True
            
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {e}")
            return False
            
    async def _solve_hcaptcha(self, page: Page) -> bool:
        """Solve hCaptcha using 2captcha service."""
        if not self.twocaptcha_key:
            logger.warning("No 2captcha API key configured")
            return False
            
        try:
            # Similar implementation to reCAPTCHA but for hCaptcha
            # This would require implementing hCaptcha-specific logic
            logger.info("hCaptcha solving not yet implemented")
            return False
            
        except Exception as e:
            logger.error(f"Error solving hCaptcha: {e}")
            return False
            
    async def _solve_turnstile(self, page: Page) -> bool:
        """Solve Cloudflare Turnstile."""
        try:
            # Turnstile often auto-solves with proper browser fingerprinting
            # Wait for automatic solving
            await asyncio.sleep(5)
            
            # Check if solved
            success = await page.evaluate("""
                () => {
                    const turnstile = document.querySelector('.cf-turnstile');
                    if (turnstile) {
                        const response = turnstile.querySelector('input[name="cf-turnstile-response"]');
                        return response && response.value !== '';
                    }
                    return false;
                }
            """)
            
            if success:
                logger.info("Turnstile solved automatically")
                return True
                
            # If not solved automatically, try clicking
            turnstile_box = page.locator('.cf-turnstile')
            if await turnstile_box.count() > 0:
                await turnstile_box.click()
                await asyncio.sleep(3)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error solving Turnstile: {e}")
            return False
            
    async def _solve_image_captcha(self, page: Page, selector: str = None) -> bool:
        """Solve image-based CAPTCHA."""
        if not self.twocaptcha_key:
            logger.warning("No 2captcha API key configured")
            return False
            
        try:
            # Find CAPTCHA image
            img_selector = selector or "img[src*='captcha'], .captcha-image, #captcha_image"
            img_element = page.locator(img_selector).first
            
            if await img_element.count() == 0:
                logger.error("CAPTCHA image not found")
                return False
                
            # Take screenshot of CAPTCHA
            captcha_image = await img_element.screenshot()
            
            # Submit to 2captcha
            captcha_id = await self._submit_image_to_2captcha(captcha_image)
            
            if not captcha_id:
                return False
                
            # Get solution
            solution = await self._get_2captcha_solution(captcha_id)
            
            if not solution:
                return False
                
            # Find input field and submit solution
            input_selector = "input[name*='captcha'], #captcha_input, .captcha-input"
            input_element = page.locator(input_selector).first
            
            if await input_element.count() > 0:
                await input_element.fill(solution)
                logger.info("Image CAPTCHA solution submitted")
                return True
            else:
                logger.error("CAPTCHA input field not found")
                return False
                
        except Exception as e:
            logger.error(f"Error solving image CAPTCHA: {e}")
            return False
            
    async def _submit_recaptcha_to_2captcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Submit reCAPTCHA to 2captcha service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://2captcha.com/in.php",
                    data={
                        "key": self.twocaptcha_key,
                        "method": "userrecaptcha",
                        "googlekey": site_key,
                        "pageurl": page_url,
                        "json": 1
                    }
                )
                
                result = response.json()
                
                if result.get("status") == 1:
                    logger.info(f"reCAPTCHA submitted to 2captcha: {result['request']}")
                    return result["request"]
                else:
                    logger.error(f"2captcha submission failed: {result}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error submitting to 2captcha: {e}")
            return None
            
    async def _submit_image_to_2captcha(self, image_data: bytes) -> Optional[str]:
        """Submit image CAPTCHA to 2captcha service."""
        try:
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://2captcha.com/in.php",
                    data={
                        "key": self.twocaptcha_key,
                        "method": "base64",
                        "body": image_b64,
                        "json": 1
                    }
                )
                
                result = response.json()
                
                if result.get("status") == 1:
                    logger.info(f"Image CAPTCHA submitted to 2captcha: {result['request']}")
                    return result["request"]
                else:
                    logger.error(f"2captcha submission failed: {result}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error submitting image to 2captcha: {e}")
            return None
            
    async def _get_2captcha_solution(self, captcha_id: str, max_attempts: int = 30) -> Optional[str]:
        """Get CAPTCHA solution from 2captcha service."""
        try:
            async with httpx.AsyncClient() as client:
                for attempt in range(max_attempts):
                    await asyncio.sleep(5)  # Wait before checking
                    
                    response = await client.get(
                        "http://2captcha.com/res.php",
                        params={
                            "key": self.twocaptcha_key,
                            "action": "get",
                            "id": captcha_id,
                            "json": 1
                        }
                    )
                    
                    result = response.json()
                    
                    if result.get("status") == 1:
                        logger.info("CAPTCHA solved by 2captcha")
                        return result["request"]
                    elif result.get("error_text") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        logger.error(f"2captcha error: {result}")
                        return None
                        
                logger.error("2captcha solution timeout")
                return None
                
        except Exception as e:
            logger.error(f"Error getting 2captcha solution: {e}")
            return None