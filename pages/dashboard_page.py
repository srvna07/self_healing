import time
import logging
from dataclasses import dataclass
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


@dataclass
class Locator:
    by: str
    value: str
    context: str  # Meaningful human description (semantic context)


class DashboardPage:


    DATE_INPUT = Locator(
        By.ID,
        "dateInput",
        "Date picker field where the user selects the transaction date for profit/loss entry"
    )

    TYPE_SELECT = Locator(
        By.ID,
        "typeInput",
        "Dropdown menu to choose whether the entry is classified as Profit or Loss"
    )

    AMOUNT_INPUT = Locator(
        By.ID,
        "amountInput",
        "Numeric input used to type the monetary value for the financial entry"
    )

    NOTE_INPUT = Locator(
        By.ID,
        "noteInput",
        "Text field for entering optional notes or additional details about the entry"
    )

    ADD_BTN = Locator(
        By.ID,
        "addBtn",
        "Primary action button that saves the new financial entry to the dashboard table"
    )

    CLEAR_BTN = Locator(
        By.ID,
        "clearBtn",
        "Button that clears all existing entries and prompts user confirmation"
    )

    ADVICE_BTN = Locator(
        By.ID,
        "adviceBtn",
        "Button that triggers AI analysis to generate financial advice based on added entries"
    )

    TOTAL_DISPLAY = Locator(
        By.ID,
        "totalDisplay",
        "Display panel showing the computed total value based on all entries"
    )

    AI_OUTPUT = Locator(
        By.ID,
        "aiOutput",
        "Text display region where AI-generated financial advice appears"
    )

    ENTRY_TABLE = Locator(
        By.ID,
        "entryTable",
        "Table element listing all user-entered financial records including date, amount, and note"
    )


    def __init__(self, driver):
        self._d = driver

    # Helper method to find element with semantic context
    def _find(self, loc: Locator):
        return self._d.find(loc.by, loc.value, loc.context)


    def open(self, file_path: str):
        url = f"file:///{file_path.replace(chr(92), '/')}"
        self._d.get(url)
        time.sleep(0.5)

    def set_date(self, date_str: str):
        el = self._find(self.DATE_INPUT)
        el.clear()
        el.send_keys(date_str)

    def set_type(self, entry_type: str):
        from selenium.webdriver.support.ui import Select
        el = self._find(self.TYPE_SELECT)
        Select(el).select_by_value(entry_type)

    def set_amount(self, amount: str):
        el = self._find(self.AMOUNT_INPUT)
        el.clear()
        el.send_keys(str(amount))

    def set_note(self, note: str):
        el = self._find(self.NOTE_INPUT)
        el.clear()
        el.send_keys(note)

    def click_add(self):
        self._find(self.ADD_BTN).click()

    def click_clear(self):
        self._find(self.CLEAR_BTN).click()
        try:
            self._d.driver.switch_to.alert.accept()
        except Exception:
            pass

    def click_get_advice(self):
        self._find(self.ADVICE_BTN).click()

    def add_entry(self, date: str, entry_type: str, amount, note: str = ""):

        self.set_date(date)
        self.set_type(entry_type)
        self.set_amount(amount)
        self.set_note(note)
        self.click_add()
        time.sleep(0.3)

    def get_total_text(self) -> str:
        return self._find(self.TOTAL_DISPLAY).text

    def get_ai_output_text(self) -> str:
        return self._find(self.AI_OUTPUT).text

    def get_entry_rows(self) -> list:

        tbody = self._find(self.ENTRY_TABLE)
        rows = []

        for tr in tbody.find_elements(By.TAG_NAME, "tr"):
            cells = tr.find_elements(By.TAG_NAME, "td")

            if len(cells) >= 2:
                rows.append({
                    "date": cells[0].text,
                    "amount": cells[1].text,
                    "note": cells[2].text if len(cells) > 2 else "",
                })

        return rows