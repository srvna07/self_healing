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
CONFIDENCE_THRESHOLD = 65


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
                logger.warning("Rate limited attempt %d/%d. Waiting %ds", attempt, GEMINI_MAX_RETRIES, wait)
                time.sleep(wait)
                delay *= 2
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error attempt %d: %s", attempt, exc)
            if attempt < GEMINI_MAX_RETRIES:
                time.sleep(delay)
                delay *= 2
        except Exception as exc:
            logger.error("Gemini call failed: %s", exc)
            return None
    return None


def _build_prompt(failed_by: str, failed_value: str, semantic_context: str, html_snippet: str) -> str:
    return (
        f"You are a Selenium expert. A locator failed to find an element.\n"
        f"Failed strategy: {failed_by}\n"
        f"Failed value: {failed_value}\n"
        f"Element description: {semantic_context}\n"
        f"Page HTML:\n{html_snippet}\n\n"
        f"Find the correct element and return ONLY a raw JSON object with no markdown, "
        f"no code fences, no explanation.\n"
        f"You must also include a confidence score (0-100) representing how certain you are "
        f"that the element you found matches the description.\n"
        f'Format: {{"by": "id or css selector or xpath", "value": "locator value", "reason": "why", "confidence": 90}}\n'
        f'If not found: {{"by": null, "value": null, "reason": "not found", "confidence": 0}}'
    )


def _log_healed(original_by, original_value, healed_by, healed_value, semantic_context, reason, confidence):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "semantic_context": semantic_context,
        "original": {"by": original_by, "value": original_value},
        "healed": {"by": healed_by, "value": healed_value},
        "confidence": confidence,
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

    logger.info("Self-healing triggered for: %s", semantic_context)

    start_time = time.time()

    html_snippet = _clean_html(driver.page_source)
    prompt = _build_prompt(failed_by, failed_value, semantic_context, html_snippet)
    raw = _ask_gemini(prompt)

    elapsed = round((time.time() - start_time) * 1000)

    if not raw:
        logger.error("Self-healing attempted and failed. Manual locator update required. | Reason: Gemini returned no response | time: %dms", elapsed)
        return None

    logger.info("Gemini raw response: %s", raw)

    raw = re.sub(r"```[a-zA-Z]*", "", raw).strip().strip("`").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Self-healing attempted and failed. Manual locator update required. | Reason: JSON parse error: %s | raw: %s | time: %dms", e, raw, elapsed)
        return None

    healed_by = result.get("by")
    healed_value = result.get("value")
    reason = result.get("reason", "")
    confidence = int(result.get("confidence", 0))

    if not healed_by or not healed_value:
        logger.error("Self-healing attempted and failed. Manual locator update required. | Reason: %s | time: %dms", reason, elapsed)
        return None

    if confidence < CONFIDENCE_THRESHOLD:
        logger.error(
            "Self-healing attempted and failed. Manual locator update required. | "
            "Reason: Confidence %d%% is below threshold %d%% for locator (%s, %s) | time: %dms",
            confidence, CONFIDENCE_THRESHOLD, healed_by, healed_value, elapsed
        )
        return None

    logger.info("Healed: (%s, %s) | confidence: %d%% | time: %dms | reason: %s", healed_by, healed_value, confidence, elapsed, reason)
    _log_healed(failed_by, failed_value, healed_by, healed_value, semantic_context, reason, confidence)
    return healed_by, healed_value