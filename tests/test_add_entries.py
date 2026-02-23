import os
import pytest
import logging

from core.driver import SelfHealingDriver
from pages.dashboard_page import DashboardPage

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

HTML_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "aimanager.html")
)

# Test dataset used across all add-entry tests
ENTRIES = [
    {"date": "01-01-2026", "type": "profit", "amount": 5000, "note": "Client A payment"},
    {"date": "01-01-2026", "type": "loss",   "amount": 1200, "note": "Server costs"},
    {"date": "01-01-2026", "type": "profit", "amount": 3000, "note": "Client B payment"},
    {"date": "01-01-2026", "type": "loss",   "amount": 500,  "note": "Office supplies"},
]


@pytest.fixture(scope="module")
def page():
    """Initializes driver and loads dashboard page."""
    driver = SelfHealingDriver()
    dp = DashboardPage(driver)
    dp.open(HTML_FILE)
    yield dp
    driver.quit()


class TestAddEntries:

    def test_page_loads(self, page):
        """Verify dashboard page is opened successfully."""
        title = page._d.title
        assert "AI" in title or "Money" in title

    def test_add_multiple_entries(self, page):
        """Add all entries and verify they appear in the table."""
        for entry in ENTRIES:
            page.add_entry(
                date=entry["date"],
                entry_type=entry["type"],
                amount=entry["amount"],
                note=entry["note"],
            )

        rows = page.get_entry_rows()
        assert len(rows) == len(ENTRIES)
    #
    # def test_total_reflects_net(self, page):
    #     """Net total should equal sum of profits minus losses."""
    #     expected_net = sum(
    #         e["amount"] if e["type"] == "profit" else -e["amount"]
    #         for e in ENTRIES
    #     )
    #
    #     total_text = page.get_total_text()
    #
    #     # Extract numeric value
    #     import re
    #     nums = re.findall(r"[\d,]+", total_text)
    #     actual_net_abs = int(nums[0].replace(",", "")) if nums else 0
    #
    #     logger.info("Expected |net|=%d, Got=%d", abs(expected_net), actual_net_abs)
    #
    #     assert actual_net_abs == abs(expected_net), (
    #         f"Net mismatch: expected {abs(expected_net)}, "
    #         f"got {actual_net_abs}"
    #     )
    #
    #
    # def test_profit_entries_shown_positive(self, page):
    #     """Profit entries should show '+' prefix."""
    #     rows = page.get_entry_rows()
    #     profit_rows = [r for r in rows if "+" in r["amount"]]
    #
    #     assert len(profit_rows) == 2, (
    #         f"Expected 2 profit rows, found {len(profit_rows)}"
    #     )
    #
    #
    # def test_loss_entries_shown_negative(self, page):
    #     """Loss entries should show '-' prefix."""
    #     rows = page.get_entry_rows()
    #     loss_rows = [r for r in rows if "-" in r["amount"]]
    #
    #     assert len(loss_rows) == 2, (
    #         f"Expected 2 loss rows, found {len(loss_rows)}"
    #     )