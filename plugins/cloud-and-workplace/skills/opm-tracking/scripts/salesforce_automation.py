#!/usr/bin/env python3
"""Salesforce Expert Request CDP Automation Runner for Cloud AI OPM.

Automates the complete end-to-end lifecycle of Expert Requests in Salesforce
Vector Lightning via Chrome DevTools Protocol.
"""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass, field
import json
import logging
import re
import sys
import time
from typing import Any, Dict, List, Optional
import requests
import websockets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sf_automation")


@dataclass
class CustomerMeeting:
    company: str
    search_term: str
    meeting_date: str  # YYYY-MM-DD
    description: str
    notes: str = ""
    er_id: Optional[str] = None
    status: str = "Pending"
    resolved_opp: Optional[str] = None
    error_reason: Optional[str] = None


class SalesforceCDPClient:
    def __init__(self, cdp_port: int = 9222):
        self.cdp_port = cdp_port
        self.ws_url: Optional[str] = None
        self.ws: Optional[Any] = None
        self._msg_id = 0

    async def connect(self):
        tabs = requests.get(f"http://localhost:{self.cdp_port}/json/list").json()
        page_tabs = [
            t for t in tabs
            if t.get("type") == "page" and (
                "force.com" in t.get("url", "") or "salesforce" in t.get("title", "").lower()
            )
        ]
        if not page_tabs:
            raise RuntimeError("No active Salesforce tab found in Chrome!")
        self.ws_url = page_tabs[0]["webSocketDebuggerUrl"]
        logger.info(f"Connecting to Salesforce tab: {page_tabs[0]['title']} ({self.ws_url})")
        self.ws = await websockets.connect(self.ws_url, max_size=25 * 1024 * 1024)

    async def send_cdp(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._msg_id += 1
        msg_id = self._msg_id
        payload = {"id": msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(payload))
        while True:
            raw = await self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == msg_id:
                return data

    async def evaluate(self, expression: str, await_promise: bool = False) -> Any:
        res = await self.send_cdp(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        )
        if "exceptionDetails" in res.get("result", {}):
            logger.warning(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get("result", {}).get("result", {}).get("value")

    async def mouse_click(self, x: float, y: float, click_count: int = 1, delay: float = 0.3):
        await self.send_cdp(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": click_count},
        )
        await self.send_cdp(
            "Input.dispatchMouseEvent",
            {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": click_count},
        )
        await asyncio.sleep(delay)

    async def type_text(self, text: str, char_delay: float = 0.04):
        for char in text:
            await self.send_cdp(
                "Input.dispatchKeyEvent",
                {"type": "keyDown", "text": char, "unmodifiedText": char},
            )
            await self.send_cdp(
                "Input.dispatchKeyEvent",
                {"type": "keyUp", "text": char, "unmodifiedText": char},
            )
            await asyncio.sleep(char_delay)

    async def capture_screenshot(self, filepath: str):
        res = await self.send_cdp("Page.captureScreenshot", {"format": "png"})
        img_b64 = res.get("result", {}).get("data", "")
        if img_b64:
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(img_b64))
            logger.info(f"Saved screenshot: {filepath}")

    async def navigate(self, url: str, wait_seconds: float = 4.0):
        logger.info(f"Navigating to: {url}")
        await self.send_cdp("Page.navigate", {"url": url})
        await asyncio.sleep(wait_seconds)


def rank_candidates(candidates: List[Dict[str, Any]], customer_name: str) -> List[Dict[str, Any]]:
    """Ranks candidates by Cloud AI relevance and open status."""
    ranked = []
    unrelated = ["applebee", "pineapple", "british airways", "appleton"]
    for cand in candidates:
        text = cand.get("text", "").lower()
        if "closed lost" in text or "closed-lost" in text:
            continue
        if any(u in text for u in unrelated):
            continue

        score = 10
        if any(term in text for term in ["agent assist", "agent platform", "cloud ai", "generative ai", "gemini"]):
            score += 100
        elif any(term in text for term in ["gcp", "google cloud", "enterprise", "renewal"]):
            score += 50

        cand_copy = dict(cand)
        cand_copy["score"] = score
        ranked.append(cand_copy)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


async def process_customer(client: SalesforceCDPClient, meeting: CustomerMeeting) -> bool:
    logger.info(f"=== Processing: {meeting.company} ({meeting.meeting_date}) ===")
    try:
        # Step 1: Navigate to clean New ER form
        await client.navigate("https://vector.lightning.force.com/lightning/o/Expert_Request__c/new", wait_seconds=3.5)

        # Step 2: Click Opportunity Name input and type search term
        logger.info(f"Searching Opportunity for: '{meeting.search_term}'...")
        # Focus/click opportunity lookup input (x=208, y=223)
        await client.mouse_click(208, 223)
        await client.type_text(meeting.search_term)
        await asyncio.sleep(2.5)

        # Step 3: Extract candidates from dropdown
        get_candidates_js = """(() => {
            function getAll(root) {
                let list = [root];
                if (root.shadowRoot) list.push(...getAll(root.shadowRoot));
                const children = Array.from(root.children || []);
                for (const c of children) list.push(...getAll(c));
                return list;
            }
            const all = getAll(document.body);
            const lookup = all.find(e => e.tagName === 'C-GENERIC-LOOKUP');
            if (!lookup) return [];
            const elements = getAll(lookup);
            const options = elements.filter(e => (
                e.getAttribute('role') === 'option' ||
                (e.className && String(e.className).includes('listbox__item')) ||
                e.tagName === 'LI'
            ));
            return options.map(o => {
                const r = o.getBoundingClientRect();
                return {
                    text: o.innerText ? o.innerText.replace(/\\n+/g, ' | ') : '',
                    rect: { x: r.left + r.width/2, y: r.top + r.height/2, width: r.width, height: r.height }
                };
            }).filter(o => o.rect.width > 0 && o.rect.height > 0 && o.text.trim().length > 0);
        })()"""
        candidates = await client.evaluate(get_candidates_js) or []
        logger.info(f"Found {len(candidates)} raw dropdown candidates.")

        ranked = rank_candidates(candidates, meeting.company)
        if not ranked:
            logger.warning(f"No valid open candidates found for '{meeting.company}' (raw: {[c.get('text') for c in candidates]})")
            meeting.error_reason = f"No open opportunity found (candidates: {[c.get('text') for c in candidates]})"
            meeting.status = "Needs Opportunity Mapping"
            return False

        # Select best candidate
        best = ranked[0]
        logger.info(f"Selecting candidate: {best['text']} at ({best['rect']['x']}, {best['rect']['y']})")
        await client.mouse_click(best["rect"]["x"], best["rect"]["y"])
        await asyncio.sleep(1.5)

        # Check if Closed Lost warning appeared
        check_error_js = """(() => {
            const text = document.body.innerText;
            if (text.includes('set as Closed Lost, please choose an open Opportunity')) {
                return 'Closed Lost Error';
            }
            return null;
        })()"""
        error_msg = await client.evaluate(check_error_js)
        if error_msg:
            logger.warning(f"Selected candidate was Closed Lost for '{meeting.company}'! Skipping.")
            meeting.error_reason = f"Candidate was Closed Lost ({best['text']})"
            meeting.status = "Needs Opportunity Mapping"
            return False

        meeting.resolved_opp = best["text"].split("|")[0].strip()

        # Step 4: Fill Type of Expertise, Expert Team, Solution, Engagement Type
        logger.info("Setting Cloud AI OPM combobox values...")
        fill_combos_js = """(() => {
            function getAll(root) {
                let list = [root];
                if (root.shadowRoot) list.push(...getAll(root.shadowRoot));
                const children = Array.from(root.children || []);
                for (const c of children) list.push(...getAll(c));
                return list;
            }
            const all = getAll(document.body);
            const comboboxes = all.filter(e => e.tagName === 'LIGHTNING-COMBOBOX');
            const typeCb = comboboxes.find(c => c.label && c.label.includes('Type of Expertise'));
            const teamCb = comboboxes.find(c => c.label && c.label.includes('Expert Team'));
            
            if (typeCb) {
                typeCb.value = 'Other SME Teams';
                typeCb.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true, detail: { value: 'Other SME Teams' } }));
            }
            if (teamCb) {
                teamCb.value = 'Cloud AI OPM (Global)';
                teamCb.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true, detail: { value: 'Cloud AI OPM (Global)' } }));
            }
            return { type: typeCb ? typeCb.value : null, team: teamCb ? teamCb.value : null };
        })()"""
        await client.evaluate(fill_combos_js)
        await asyncio.sleep(1.0)

        # Step 5: Fill Description and Click Save
        logger.info(f"Setting Description: '{meeting.description}' and clicking Save...")
        save_js = f"""(() => {{
            function getAll(root) {{
                let list = [root];
                if (root.shadowRoot) list.push(...getAll(root.shadowRoot));
                const children = Array.from(root.children || []);
                for (const c of children) list.push(...getAll(c));
                return list;
            }}
            const all = getAll(document.body);
            const ta = all.find(e => e.tagName === 'LIGHTNING-TEXTAREA');
            if (ta) {{
                ta.value = {json.dumps(meeting.description)};
                ta.dispatchEvent(new CustomEvent('change', {{ bubbles: true, composed: true, detail: {{ value: ta.value }} }}));
                ta.dispatchEvent(new CustomEvent('input', {{ bubbles: true, composed: true, detail: {{ value: ta.value }} }}));
            }}
            const saveBtn = all.find(e => e.tagName === 'BUTTON' && e.innerText && e.innerText.trim() === 'Save');
            if (saveBtn) {{
                saveBtn.click();
                return true;
            }}
            return false;
        }})()"""
        await client.evaluate(save_js)
        await asyncio.sleep(4.0)

        # Extract record ID
        url_info = await client.evaluate("JSON.stringify({ url: window.location.href, title: document.title })")
        info = json.loads(url_info or "{}")
        url = info.get("url", "")
        title = info.get("title", "")
        logger.info(f"Current page after save: URL={url}, Title={title}")

        er_match = re.search(r"ER-\d+", title) or re.search(r"ER-\d+", url)
        if not er_match:
            # Check body text
            body_er = await client.evaluate("document.body.innerText.match(/ER-\\d+/)")
            if body_er:
                er_id = body_er[0]
            else:
                logger.error(f"Failed to find ER ID after save for {meeting.company}! Title: {title}")
                meeting.error_reason = f"Saved but ER ID not found in page (Title: {title})"
                meeting.status = "Failed Save Verification"
                return False
        else:
            er_id = er_match.group(0)

        meeting.er_id = er_id
        logger.info(f"Successfully created: {er_id} for {meeting.company}")

        # Step 6: Assign To Me
        logger.info(f"Clicking Assign To Me for {er_id}...")
        # The Assign To Me button is at x=930, y=133
        await client.mouse_click(930, 133)
        await asyncio.sleep(2.5)

        # Step 7: Open Start Date edit, set Status to Completed, set Dates, and Save
        logger.info(f"Setting dates ({meeting.meeting_date}) and status to Completed...")
        edit_dates_js = f"""(() => {{
            function getAll(root) {{
                let list = [root];
                if (root.shadowRoot) list.push(...getAll(root.shadowRoot));
                const children = Array.from(root.children || []);
                for (const c of children) list.push(...getAll(c));
                return list;
            }}
            const all = getAll(document.body);
            const btn = all.find(e => e.tagName === 'BUTTON' && (e.title === 'Edit Request Start Date' || (e.innerText && e.innerText.includes('Edit Request Start Date'))));
            if (btn) {{
                btn.click();
                return true;
            }}
            return false;
        }})()"""
        await client.evaluate(edit_dates_js)
        await asyncio.sleep(1.5)

        set_and_save_dates_js = f"""(() => {{
            function getAll(root) {{
                let list = [root];
                if (root.shadowRoot) list.push(...getAll(root.shadowRoot));
                const children = Array.from(root.children || []);
                for (const c of children) list.push(...getAll(c));
                return list;
            }}
            const all = getAll(document.body);
            const comboboxes = all.filter(e => e.tagName === 'LIGHTNING-COMBOBOX');
            
            // Set Status to Completed
            const statusCb = comboboxes.find(c => c.label === 'Status');
            if (statusCb) {{
                statusCb.value = 'Completed';
                statusCb.dispatchEvent(new CustomEvent('change', {{ bubbles: true, composed: true, detail: {{ value: 'Completed' }} }}));
            }}
            
            // Set Start Date & End Date
            const startInput = all.find(e => e.tagName === 'LIGHTNING-INPUT' && e.label === 'Request Start Date');
            const endInput = all.find(e => e.tagName === 'LIGHTNING-INPUT' && e.label === 'Request End Date');
            
            if (startInput) {{
                startInput.value = '{meeting.meeting_date}';
                startInput.dispatchEvent(new CustomEvent('change', {{ bubbles: true, composed: true, detail: {{ value: '{meeting.meeting_date}' }} }}));
                startInput.dispatchEvent(new CustomEvent('input', {{ bubbles: true, composed: true, detail: {{ value: '{meeting.meeting_date}' }} }}));
            }}
            if (endInput) {{
                endInput.value = '{meeting.meeting_date}';
                endInput.dispatchEvent(new CustomEvent('change', {{ bubbles: true, composed: true, detail: {{ value: '{meeting.meeting_date}' }} }}));
                endInput.dispatchEvent(new CustomEvent('input', {{ bubbles: true, composed: true, detail: {{ value: '{meeting.meeting_date}' }} }}));
            }}
            
            const saveBtn = all.find(e => e.tagName === 'BUTTON' && e.name === 'SaveEdit');
            if (saveBtn) {{
                saveBtn.click();
                return true;
            }}
            return false;
        }})()"""
        await client.evaluate(set_and_save_dates_js)
        await asyncio.sleep(2.5)

        meeting.status = "Completed"
        logger.info(f"SUCCESS: {meeting.company} -> {meeting.er_id} ({meeting.status}, {meeting.meeting_date})")
        return True

    except Exception as e:
        logger.error(f"Error processing {meeting.company}: {e}", exc_info=True)
        meeting.error_reason = str(e)
        meeting.status = "Error"
        return False


async def run_batch(meetings: List[CustomerMeeting]):
    client = SalesforceCDPClient()
    await client.connect()

    results = []
    for m in meetings:
        success = await process_customer(client, m)
        results.append(m)
        await asyncio.sleep(1.0)

    logger.info("=========================================")
    logger.info("BATCH RUN COMPLETE SUMMARY:")
    for r in results:
        logger.info(f"  [{r.status}] {r.company}: {r.er_id or 'N/A'} (Opp: {r.resolved_opp or 'None'}) - {r.error_reason or ''}")
    logger.info("=========================================")


if __name__ == "__main__":
    test_meetings = [
        CustomerMeeting(
            company="Bank of London",
            search_term="Bank of London",
            meeting_date="2026-08-18",
            description="Agent Platform - Customer Meeting / Technical Sync",
        ),
        CustomerMeeting(
            company="JetBrains",
            search_term="JetBrains",
            meeting_date="2026-08-11",
            description="Agent Platform - Customer Meeting / Developer Tools",
        ),
    ]
    asyncio.run(run_batch(test_meetings))
