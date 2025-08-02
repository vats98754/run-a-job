"""Account creation automation for various platforms."""

import asyncio
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from run_a_job.automation.browser import BrowserAutomation
from run_a_job.config.logging import get_logger


logger = get_logger(__name__)


@dataclass
class AccountTemplate:
    """Template for account creation."""
    platform: str
    signup_url: str
    fields: Dict[str, str]  # field_name -> selector
    submit_button: str
    success_indicator: str
    requires_captcha: bool = False
    requires_email_verification: bool = False


class AccountCreator:
    """Automated account creation for various platforms."""
    
    def __init__(self):
        """Initialize account creator."""
        self.templates = self._load_platform_templates()
        
    async def create_account(
        self,
        platform: str,
        account_data: Dict[str, Any],
        use_existing_browser: Optional[BrowserAutomation] = None
    ) -> Dict[str, Any]:
        """Create an account on the specified platform.
        
        Args:
            platform: Platform name (e.g., 'twitter', 'instagram')
            account_data: Account information (username, email, password, etc.)
            use_existing_browser: Optional existing browser instance
            
        Returns:
            Creation result with status and details
        """
        template = self.templates.get(platform.lower())
        if not template:
            raise ValueError(f"Platform '{platform}' not supported")
            
        browser = use_existing_browser
        should_close = False
        
        if not browser:
            browser = BrowserAutomation()
            should_close = True
            
        try:
            if should_close:
                await browser.start()
                
            logger.info(f"Creating account on {platform}")
            
            # Navigate to signup page
            await browser.navigate(template.signup_url)
            
            # Handle potential Cloudflare
            await browser.bypass_cloudflare()
            
            # Fill form fields
            for field_name, selector in template.fields.items():
                if field_name in account_data:
                    value = account_data[field_name]
                    logger.debug(f"Filling {field_name} field")
                    await browser.type_text(selector, str(value))
                    
                    # Add random delay between fields
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
            # Handle CAPTCHA if required
            if template.requires_captcha:
                logger.info("Attempting to solve CAPTCHA")
                captcha_solved = await browser.solve_captcha()
                if not captcha_solved:
                    return {
                        "success": False,
                        "error": "Failed to solve CAPTCHA",
                        "platform": platform
                    }
                    
            # Submit form
            await browser.click(template.submit_button)
            
            # Wait for result
            await asyncio.sleep(3)
            
            # Check for success
            try:
                await browser.wait_for_element(template.success_indicator, timeout=10000)
                success = True
                error = None
            except Exception:
                # Check for error messages
                error = await self._detect_signup_errors(browser, platform)
                success = False
                
            result = {
                "success": success,
                "platform": platform,
                "account_data": account_data,
                "error": error
            }
            
            # Handle email verification if required
            if success and template.requires_email_verification:
                result["requires_email_verification"] = True
                logger.info("Account created but requires email verification")
                
            logger.info(f"Account creation {'successful' if success else 'failed'} for {platform}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating account on {platform}: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform
            }
            
        finally:
            if should_close and browser:
                await browser.close()
                
    async def _detect_signup_errors(self, browser: BrowserAutomation, platform: str) -> Optional[str]:
        """Detect common signup errors."""
        error_selectors = [
            ".error-message",
            ".alert-danger",
            "[data-testid='error']",
            ".form-error",
            ".invalid-feedback",
            ".error-text"
        ]
        
        for selector in error_selectors:
            try:
                if await browser.page.locator(selector).count() > 0:
                    error_text = await browser.get_text(selector)
                    if error_text.strip():
                        return error_text.strip()
            except Exception:
                continue
                
        return "Unknown error occurred during signup"
        
    def _load_platform_templates(self) -> Dict[str, AccountTemplate]:
        """Load platform-specific signup templates."""
        templates = {}
        
        # Twitter/X template
        templates['twitter'] = AccountTemplate(
            platform='twitter',
            signup_url='https://twitter.com/i/flow/signup',
            fields={
                'name': '[name="name"]',
                'email': '[name="email"]',
                'password': '[name="password"]'
            },
            submit_button='[data-testid="signupButton"]',
            success_indicator='[data-testid="confirmationCode"]',
            requires_captcha=True,
            requires_email_verification=True
        )
        
        # Instagram template
        templates['instagram'] = AccountTemplate(
            platform='instagram',
            signup_url='https://www.instagram.com/accounts/emailsignup/',
            fields={
                'email': '[name="emailOrPhone"]',
                'fullName': '[name="fullName"]',
                'username': '[name="username"]',
                'password': '[name="password"]'
            },
            submit_button='button[type="submit"]',
            success_indicator='[data-testid="confirmEmail"]',
            requires_captcha=True,
            requires_email_verification=True
        )
        
        # Reddit template
        templates['reddit'] = AccountTemplate(
            platform='reddit',
            signup_url='https://www.reddit.com/register/',
            fields={
                'email': '#regEmail',
                'username': '#regUsername',
                'password': '#regPassword'
            },
            submit_button='button[type="submit"]',
            success_indicator='.success-message',
            requires_captcha=True,
            requires_email_verification=True
        )
        
        # GitHub template
        templates['github'] = AccountTemplate(
            platform='github',
            signup_url='https://github.com/join',
            fields={
                'username': '#user_login',
                'email': '#user_email',
                'password': '#user_password'
            },
            submit_button='[data-signup-form-button]',
            success_indicator='[data-testid="signup-success"]',
            requires_captcha=True,
            requires_email_verification=True
        )
        
        return templates
        
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms."""
        return list(self.templates.keys())
        
    def get_required_fields(self, platform: str) -> List[str]:
        """Get required fields for a platform."""
        template = self.templates.get(platform.lower())
        if not template:
            raise ValueError(f"Platform '{platform}' not supported")
            
        return list(template.fields.keys())
        
    async def batch_create_accounts(
        self,
        platform: str,
        accounts_data: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """Create multiple accounts in batches.
        
        Args:
            platform: Platform name
            accounts_data: List of account data dictionaries
            max_concurrent: Maximum concurrent account creations
            
        Returns:
            List of creation results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def create_single(account_data):
            async with semaphore:
                # Add random delay to avoid being flagged
                await asyncio.sleep(random.uniform(1, 5))
                return await self.create_account(platform, account_data)
                
        # Execute all creations concurrently
        tasks = [create_single(data) for data in accounts_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "success": False,
                    "error": str(result),
                    "platform": platform,
                    "account_data": accounts_data[i]
                })
            else:
                final_results.append(result)
                
        return final_results