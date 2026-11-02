#!/usr/bin/env python3
"""
Brand DNA & CSS Token Extractor.
Crawls a target website, captures viewport/full-page screenshots using headless Chrome,
and extracts DOM CSS styles, :root variables, and brand typography.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import shutil

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Warning: missing requests or bs4 ({e}). Basic extraction will be used.", file=sys.stderr)
    requests = None
    BeautifulSoup = None

def find_chrome_binary():
    for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
        path = shutil.which(name)
        if path:
            return path
    if os.path.exists("/usr/bin/google-chrome"):
        return "/usr/bin/google-chrome"
    return None

def capture_chrome_screenshots(url, output_dir, chrome_bin):
    os.makedirs(output_dir, exist_ok=True)
    vp_path = os.path.join(output_dir, "source_screenshot_1_viewport.png")
    full_path = os.path.join(output_dir, "source_screenshot_1_full.png")
    
    # 1. Viewport screenshot (1920x1080)
    cmd_vp = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1920,1080",
        f"--screenshot={vp_path}",
        url
    ]
    try:
        subprocess.run(cmd_vp, check=True, timeout=25, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[extract] Chrome viewport capture failed: {e}", file=sys.stderr)
        vp_path = None

    # 2. Full-page screenshot (simulated via larger virtual height)
    cmd_full = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1920,4000",
        f"--screenshot={full_path}",
        url
    ]
    try:
        subprocess.run(cmd_full, check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[extract] Chrome full-page capture failed: {e}", file=sys.stderr)
        full_path = None

    return vp_path, full_path

def rgb_to_hex(rgb_str):
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb_str.strip())
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"#{r:02x}{g:02x}{b:02x}".upper()
    return rgb_str

def extract_css_tokens(url):
    tokens = {
        "colors": {},
        "typography": {},
        "spacing": {},
        "rounded": {},
        "internal_links": []
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    if not requests or not BeautifulSoup:
        return tokens

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"[extract] HTTP request failed for {url}: {e}", file=sys.stderr)
        return tokens

    soup = BeautifulSoup(html, "html.parser")

    # 1. Extract internal links
    parsed_base = urllib.parse.urlparse(url)
    base_netloc = parsed_base.netloc
    seen_links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        joined = urllib.parse.urljoin(url, href)
        p = urllib.parse.urlparse(joined)
        if p.netloc == base_netloc and p.path not in seen_links and p.path not in ["", "/"]:
            seen_links.add(p.path)
            text = a.get_text().strip().lower()
            tokens["internal_links"].append({"url": joined, "text": text})

    # Filter candidate links
    candidate_keywords = ["about", "product", "feature", "pricing", "design", "company"]
    candidates = [
        l for l in tokens["internal_links"]
        if any(k in l["text"] or k in l["url"].lower() for k in candidate_keywords)
    ]
    tokens["candidate_internal_pages"] = candidates[:3]

    # 2. Extract inline styles and CSS rules from <style> blocks
    css_text = ""
    for style in soup.find_all("style"):
        if style.string:
            css_text += style.string + "\n"

    # Also fetch external stylesheets on same origin / CDN (up to 3)
    css_links = []
    for link in soup.find_all("link", rel="stylesheet", href=True):
        css_links.append(urllib.parse.urljoin(url, link["href"]))

    for css_url in css_links[:3]:
        try:
            r = requests.get(css_url, headers=headers, timeout=5)
            if r.status_code == 200:
                css_text += r.text + "\n"
        except Exception:
            pass

    # Extract :root variables
    root_matches = re.findall(r':root\s*\{([^}]+)\}', css_text, re.MULTILINE | re.DOTALL)
    for root_block in root_matches:
        var_pairs = re.findall(r'(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+);', root_block)
        for var_name, var_val in var_pairs:
            var_val = var_val.strip()
            # Color
            if var_val.startswith("#"):
                tokens["colors"][var_name] = var_val.upper()
            elif var_val.startswith("rgb"):
                tokens["colors"][var_name] = rgb_to_hex(var_val)
            # Spacing
            elif any(k in var_name.lower() for k in ["space", "spacing", "gap", "padding", "margin"]):
                tokens["spacing"][var_name] = var_val
            # Radius / Rounded
            elif any(k in var_name.lower() for k in ["radius", "rounded", "corner"]):
                tokens["rounded"][var_name] = var_val
            # Font family
            elif "font" in var_name.lower() and not any(unit in var_val for unit in ["px", "rem", "em"]):
                tokens["typography"][var_name] = var_val.replace("'", "").replace('"', "")

    # If no colors extracted, extract common hex codes from all CSS
    if len(tokens["colors"]) < 3:
        hexes = set(re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', css_text))
        for idx, h in enumerate(sorted(hexes)[:8]):
            tokens["colors"][f"palette_{idx+1}"] = h.upper()

    return tokens

def main():
    parser = argparse.ArgumentParser(description="Extract Brand DNA, screenshots, and CSS tokens from a website")
    parser.add_argument("--url", required=True, help="Target website URL")
    parser.add_argument("--output", default="./brand-output", help="Output directory for screenshots and tokens")
    parser.add_argument("--json", action="store_true", help="Print extracted tokens as JSON to stdout")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    chrome_bin = find_chrome_binary()

    screenshots = []
    if chrome_bin:
        print(f"[extract] Found Chrome at {chrome_bin}. Capturing screenshots...", file=sys.stderr)
        vp, full = capture_chrome_screenshots(args.url, args.output, chrome_bin)
        if vp and os.path.exists(vp):
            screenshots.append(vp)
        if full and os.path.exists(full):
            screenshots.append(full)
    else:
        print("[extract] Google Chrome not found. Skipping screenshot capture.", file=sys.stderr)

    print(f"[extract] Parsing DOM and CSS tokens from {args.url}...", file=sys.stderr)
    tokens = extract_css_tokens(args.url)
    tokens["url"] = args.url
    tokens["screenshots"] = screenshots

    tokens_path = os.path.join(args.output, "extracted_css_tokens.json")
    with open(tokens_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

    print(f"[extract] ✓ Successfully extracted tokens to {tokens_path}", file=sys.stderr)
    if screenshots:
        print(f"[extract] ✓ Captured {len(screenshots)} screenshot(s)", file=sys.stderr)

    if args.json:
        print(json.dumps(tokens, indent=2))

if __name__ == "__main__":
    main()
