import json
import re
import os
import time
import logging
from datetime import datetime
from typing import Optional, Tuple
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL, SELF_HEALING_ENABLED

logger = logging.getLogger(__name__)

HEALED_LOG = os.path.join(os.path.dirname(__file__), "..", "healed_locators.json")
GEMINI_MAX_RETRIES = 4
GEMINI_RETRY_DELAY = 5


def _gemini_url() -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )


def _clean_html(page_source: str) -> str:
    cleaned = re.sub(r"<script[\s\S]*?</script>", "", page_source, flags=re.IGNORECASE)
    cleaned = re.sub(r"<style[\s\S]*?</style>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", cleaned, re.IGNORECASE)
    if body_match:
        cleaned = body_match.group(1)
    return cleaned[:6000]


def _ask_gemini(prompt: str) -> Optional[str]:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
    }
    delay = GEMINI_RETRY_DELAY
    for attempt in range(1, GEMINI_MAX_RETRIES + 1):
        try:
            resp = requests.post(_gemini_url(), json=body, timeout=30)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", delay))
                wait = max(retry_after, delay)
                time.sleep(wait)
                delay *= 2
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            if attempt < GEMINI_MAX_RETRIES:
                time.sleep(delay)
                delay *= 2
            else:
                return None
    return None


def _build_prompt(failed_by: str, failed_value: str, semantic_context: str, html_snippet: str) -> str:
    return f"""
Failed locator:
Strategy: {failed_by}
Value: {failed_value}
Context: {semantic_context}
HTML: {html_snippet}

Return only JSON: {{"by": "", "value": "", "reason": ""}}
If not found: {{"by": null, "value": null, "reason": "not found"}}
"""


def _log_healed(original_by, original_value, healed_by, healed_value, semantic_context, reason):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "semantic_context": semantic_context,
        "original": {"by": original_by, "value": original_value},
        "healed": {"by": healed_by, "value": healed_value},
        "reason": reason,
    }

    records = []
    if os.path.exists(HEALED_LOG):
        try:
            with open(HEALED_LOG) as f:
                records = json.load(f)
        except Exception:
            records = []

    records.append(entry)
    with open(HEALED_LOG, "w") as f:
        json.dump(records, f, indent=2)


def heal(driver, failed_by: str, failed_value: str, semantic_context: str) -> Optional[Tuple[str, str]]:
    if not SELF_HEALING_ENABLED:
        return None

    html_snippet = _clean_html(driver.page_source)
    prompt = _build_prompt(failed_by, failed_value, semantic_context, html_snippet)
    raw = _ask_gemini(prompt)

    if not raw:
        return None

    raw = re.sub(r"\n[a-z]*", "", raw).strip().strip("`").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return None

    healed_by = result.get("by")
    healed_value = result.get("value")
    reason = result.get("reason", "")

    if not healed_by or not healed_value:
        return None

    _log_healed(failed_by, failed_value, healed_by, healed_value, semantic_context, reason)
    return healed_by, healed_value