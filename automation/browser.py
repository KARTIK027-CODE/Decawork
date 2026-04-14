import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext, Browser
from config.logger import logger
from config.settings import settings

class BrowserAutomation:
    """Encapsulates Playwright interactions mapping to human-like behavior and robust error propagation."""
    
    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.HEADLESS_MODE, 
            slow_mo=200 # Human-like perception delay built-in
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        logger.info("Browser automation started", extra={"context": {"headless": settings.HEADLESS_MODE}})

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser automation cleanly terminated")

    async def navigate(self, url: str):
        logger.info(f"Navigating to {url}")
        # Using strict networkidle helps prevent operating on incomplete DOMs
        await self.page.goto(url, wait_until="networkidle", timeout=settings.DEFAULT_TIMEOUT_MS)

    async def type_text(self, selector: str, text: str):
        logger.info(f"Typing text into selector: {selector}")
        await self.page.wait_for_selector(selector, state="visible", timeout=settings.DEFAULT_TIMEOUT_MS)
        await self.page.fill(selector, "")
        # Emulate keystrokes individually
        await self.page.type(selector, text, delay=50)

    async def click(self, selector: str):
        logger.info(f"Clicking selector: {selector}")
        await self.page.wait_for_selector(selector, state="visible", timeout=settings.DEFAULT_TIMEOUT_MS)
        await self.page.click(selector)

    async def exists(self, selector: str) -> bool:
        """Fast non-blocking check if element is attached to DOM."""
        count = await self.page.locator(selector).count()
        return count > 0

    async def wait_for_text(self, text: str):
        logger.info(f"Awaiting text existence text='{text}'")
        await self.page.wait_for_selector(f"text='{text}'", state="visible", timeout=settings.DEFAULT_TIMEOUT_MS)

    async def execute_javascript(self, script: str):
        return await self.page.evaluate(script)
