import os, asyncio
from pathlib import Path

# Official Content Posting API requires access + OAuth. See docs.
# Fallback: Playwright to automate web upload using saved session.

async def playwright_upload(video_path: str, caption: str):
    from playwright.async_api import async_playwright
    storage_state = os.getenv("TIKTOK_STORAGE_STATE", "secrets/tiktok_state.json")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=storage_state if Path(storage_state).exists() else None)
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/upload?lang=en")
        # If not logged in, user must log in manually once; then save storage
        # Upload file
        input_file = page.locator('input[type="file"]')
        await input_file.set_input_files(video_path)
        # Caption textarea
        await page.wait_for_selector("textarea")
        await page.fill("textarea", caption[:2200])
        # Click Post (selector may vary by region; adjust if necessary)
        # Many locales use data-e2e="post-button"
        try:
            await page.click('[data-e2e="post-button"]', timeout=60000)
        except:
            # Try alternative button text
            await page.get_by_role("button", name="Post").click(timeout=60000)
        # Give some time to process
        await page.wait_for_timeout(10000)
        # Save storage for reuse
        await context.storage_state(path=storage_state)
        await browser.close()
