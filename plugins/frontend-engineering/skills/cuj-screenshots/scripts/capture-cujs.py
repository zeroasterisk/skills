#!/usr/bin/env python3
"""
CUJ Screenshot Capture Script

Captures Critical User Journey screenshots and generates GIFs.
Designed to run against a local dev server.

Usage:
    uv run --with playwright python capture-cujs.py

Requirements:
    - Python 3.10+
    - uv (recommended) or pip
    - Playwright with Chromium browser
    - ImageMagick (for GIF creation)
    - Your app running locally
"""

import asyncio
import os
import shutil
import subprocess
import sys


def check_prerequisites() -> list[str]:
    """
    Verify all prerequisites are installed.
    Returns list of error messages (empty if all good).
    """
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        errors.append(
            f"❌ Python 3.10+ required (you have {sys.version_info.major}.{sys.version_info.minor})\n"
            f"   Fix: Install Python 3.10+ from https://python.org"
        )
    
    # Check for ImageMagick (convert command)
    if not shutil.which("convert"):
        errors.append(
            "❌ ImageMagick not found (needed for GIF creation)\n"
            "   Fix (macOS):  brew install imagemagick\n"
            "   Fix (Ubuntu): sudo apt install imagemagick\n"
            "   Fix (Fedora): sudo dnf install ImageMagick"
        )
    
    # Check for Playwright
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        errors.append(
            "❌ Playwright not installed\n"
            "   Fix: pip install playwright\n"
            "   Or:  uv run --with playwright python capture-cujs.py"
        )
        return errors  # Can't check browser without playwright
    
    # Check for Chromium browser
    try:
        # Playwright stores browsers in a known location
        import playwright
        playwright_path = os.path.dirname(playwright.__file__)
        # Quick check - try to get browser path
        result = subprocess.run(
            [sys.executable, "-c", 
             "from playwright.sync_api import sync_playwright; "
             "p = sync_playwright().start(); "
             "b = p.chromium.executable_path; "
             "print(b); p.stop()"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise Exception("Browser not found")
    except Exception:
        errors.append(
            "❌ Playwright Chromium browser not installed\n"
            "   Fix: playwright install chromium\n"
            "   Or:  uv run --with playwright playwright install chromium"
        )
    
    return errors


def check_server(url: str, name: str) -> str | None:
    """Check if a server is responding. Returns error message or None."""
    import urllib.request
    import urllib.error
    
    try:
        urllib.request.urlopen(url, timeout=3)
        return None
    except urllib.error.URLError:
        return (
            f"❌ {name} not responding at {url}\n"
            f"   Fix: Start your {name.lower()} before running this script"
        )
    except Exception as e:
        return f"❌ {name} check failed: {e}"


def verify_environment(frontend_url: str = "http://localhost:5173", 
                       backend_url: str | None = "http://localhost:8000") -> bool:
    """
    Verify all prerequisites and servers are ready.
    Prints helpful error messages and returns False if anything is missing.
    """
    print("🔍 Checking prerequisites...\n")
    
    # Check tools
    errors = check_prerequisites()
    
    # Check servers
    frontend_error = check_server(frontend_url, "Frontend")
    if frontend_error:
        errors.append(frontend_error)
    
    if backend_url:
        backend_error = check_server(backend_url, "Backend")
        if backend_error:
            errors.append(backend_error)
    
    # Report results
    if errors:
        print("=" * 60)
        print("⚠️  SETUP INCOMPLETE - Please fix the following:\n")
        print("=" * 60)
        for error in errors:
            print(f"\n{error}")
        print("\n" + "=" * 60)
        print("\n📚 Full setup guide: See SKILL.md in this directory")
        print("=" * 60 + "\n")
        return False
    
    print("✅ All prerequisites satisfied!\n")
    return True


# Import playwright after checks (so we can report missing dependency nicely)
try:
    from playwright.async_api import async_playwright
except ImportError:
    # Will be caught by check_prerequisites
    pass

# Configuration
VIEWPORT_MOBILE = {"width": 390, "height": 844}
DEVICE_SCALE = 2
BASE_URL = "http://localhost:5173"
OUTPUT_BASE = "/tmp/cuj-screenshots"
GIF_OUTPUT = "docs/gifs"


async def capture_cuj(
    name: str,
    steps: list[dict],
    viewport: dict = VIEWPORT_MOBILE,
    scale: float = DEVICE_SCALE,
):
    """
    Capture a CUJ with the given steps.
    
    Args:
        name: CUJ name (used for output folder)
        steps: List of step dicts with 'action', 'screenshot', and optional params
        viewport: Browser viewport dimensions
        scale: Device scale factor
    
    Returns:
        Path to output directory
    """
    output_dir = f"{OUTPUT_BASE}/{name}"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport=viewport,
            device_scale_factor=scale
        )
        page = await context.new_page()
        
        for i, step in enumerate(steps):
            action = step.get("action", "screenshot")
            screenshot_name = step.get("screenshot", f"{i+1:02d}-step.png")
            
            try:
                if action == "goto":
                    url = step.get("url", BASE_URL)
                    await page.goto(url)
                    await page.wait_for_timeout(step.get("wait", 1500))
                
                elif action == "click":
                    selector = step["selector"]
                    await page.click(selector)
                    await page.wait_for_timeout(step.get("wait", 1000))
                
                elif action == "fill":
                    selector = step["selector"]
                    value = step["value"]
                    await page.fill(selector, value)
                    await page.wait_for_timeout(step.get("wait", 300))
                
                elif action == "scroll":
                    x = step.get("x", 0)
                    y = step.get("y", 300)
                    await page.evaluate(f"window.scrollBy({x}, {y})")
                    await page.wait_for_timeout(step.get("wait", 500))
                
                elif action == "wait":
                    await page.wait_for_timeout(step.get("wait", 1000))
                
                elif action == "screenshot":
                    pass  # Just take screenshot
                
                # Take screenshot after action
                path = f"{output_dir}/{screenshot_name}"
                await page.screenshot(path=path)
                print(f"✓ {name}: {screenshot_name}")
                
            except Exception as e:
                print(f"✗ {name}: {screenshot_name} - Error: {e}")
                # Screenshot the error state
                await page.screenshot(path=f"{output_dir}/{screenshot_name.replace('.png', '-error.png')}")
        
        await browser.close()
    
    return output_dir


def create_gif(input_dir: str, output_path: str, delay: int = 150):
    """
    Create an animated GIF from screenshots in a directory.
    
    Args:
        input_dir: Directory containing numbered PNG files
        output_path: Output GIF path
        delay: Frame delay in hundredths of a second (150 = 1.5s)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cmd = [
        "convert",
        "-delay", str(delay),
        "-loop", "0",
        f"{input_dir}/*.png",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ Created GIF: {output_path}")
    else:
        print(f"✗ GIF creation failed: {result.stderr}")


# ============================================================
# Define your CUJs here
# ============================================================

CUJ_APP_TOUR = {
    "name": "cuj1-app-tour",
    "steps": [
        {"action": "goto", "url": BASE_URL, "wait": 1500, "screenshot": "01-activity-tab.png"},
        {"action": "scroll", "y": 200, "wait": 500, "screenshot": "02-scroll-tasks.png"},
        {"action": "click", "selector": "text=Live", "wait": 1000, "screenshot": "03-live-tab.png"},
        {"action": "click", "selector": "text=Activity", "wait": 1000, "screenshot": "04-back-to-activity.png"},
    ]
}

CUJ_CREATE_TASK = {
    "name": "cuj2-create-task",
    "steps": [
        {"action": "goto", "url": BASE_URL, "wait": 1500, "screenshot": "01-initial.png"},
        {"action": "click", "selector": "button:has-text('Plan')", "wait": 500, "screenshot": "02-plan-form.png"},
        {"action": "fill", "selector": "input", "value": "My Demo Plan", "wait": 300, "screenshot": "03-plan-filled.png"},
        {"action": "click", "selector": "button:has-text('Add')", "wait": 1000, "screenshot": "04-plan-created.png"},
        {"action": "click", "selector": "button:has-text('Task')", "wait": 500, "screenshot": "05-task-form.png"},
        {"action": "fill", "selector": "input", "value": "My First Task", "wait": 300, "screenshot": "06-task-filled.png"},
        {"action": "click", "selector": "button:has-text('Add')", "wait": 1000, "screenshot": "07-task-created.png"},
    ]
}

CUJ_MOVE_TASK = {
    "name": "cuj3-move-task",
    "steps": [
        {"action": "goto", "url": BASE_URL, "wait": 1500, "screenshot": "01-task-in-backlog.png"},
        {"action": "click", "selector": "button:has-text('Start')", "wait": 1000, "screenshot": "02-task-started.png"},
        {"action": "scroll", "x": 200, "y": 0, "wait": 500, "screenshot": "03-in-progress.png"},
        {"action": "click", "selector": "button:has-text('Done')", "wait": 1000, "screenshot": "04-task-completed.png"},
    ]
}


async def main():
    """Capture all CUJs and create GIFs."""
    
    # Verify environment before starting
    if not verify_environment(frontend_url=BASE_URL, backend_url="http://localhost:8000"):
        sys.exit(1)
    
    cujs = [CUJ_APP_TOUR, CUJ_CREATE_TASK, CUJ_MOVE_TASK]
    
    for cuj in cujs:
        print(f"\n📸 Capturing {cuj['name']}...")
        output_dir = await capture_cuj(cuj["name"], cuj["steps"])
        
        gif_path = f"{GIF_OUTPUT}/{cuj['name']}.gif"
        create_gif(output_dir, gif_path)
    
    print("\n✅ All CUJs captured!")


if __name__ == "__main__":
    asyncio.run(main())
