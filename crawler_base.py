import time
import random
from abc import ABC, abstractmethod
from typing import List, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth
import logging

from models import BusinessDetail
import config

logger = logging.getLogger("CrawlerBase")

class BaseCrawler(ABC):
    def __init__(self, city: str, category: str):
        self.city = city
        self.category = category
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def setup_browser(self) -> Page:
        """Initializes Playwright browser with anti-bot bypass settings."""
        self.playwright = sync_playwright().start()
        
        # Select random user agent
        ua = random.choice(config.USER_AGENTS)
        
        # Configure proxy if available
        proxy_opts = None
        if config.PROXY_SERVER:
            # Expected format: http://user:pass@host:port
            proxy_opts = {"server": config.PROXY_SERVER}
            
        logger.info(f"Launching browser (Headless: {config.HEADLESS}) with User-Agent: {ua}")
        
        self.browser = self.playwright.chromium.launch(
            headless=config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-http2"
            ]
        )
        
        self.context = self.browser.new_context(
            user_agent=ua,
            viewport={"width": 1280, "height": 800},
            proxy=proxy_opts,
            ignore_https_errors=True
        )
        
        # Enable stealth
        self.page = self.context.new_page()
        Stealth().apply_stealth_sync(self.page)
        
        # Set default timeout
        self.page.set_default_timeout(config.REQUEST_TIMEOUT)
        
        return self.page

    def close_browser(self):
        """Cleans up Playwright resources."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def random_delay(self, min_s: float = 1.0, max_s: float = 3.0):
        """Sleeps for a random duration to mimic human behavior."""
        delay = random.uniform(min_s, max_s)
        time.sleep(delay)

    @abstractmethod
    def run(self) -> List[BusinessDetail]:
        """Main execution flow for the crawler."""
        pass
