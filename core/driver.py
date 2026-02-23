import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from config import HEADLESS, IMPLICIT_WAIT, EXPLICIT_WAIT
from core.healer import heal

logger = logging.getLogger(__name__)


class SelfHealingDriver:
    def __init__(self):
        opts = Options()
        if HEADLESS:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1280,900")

        self._driver = webdriver.Chrome(options=opts)
        self._driver.implicitly_wait(IMPLICIT_WAIT)
        logger.info("ChromeDriver started")

    def find(self, by: str, value: str, semantic_context: str = ""):

        self._driver.implicitly_wait(0)
        try:
            return self._driver.find_element(by, value)
        except (NoSuchElementException, StaleElementReferenceException):
            logger.warning("Locator failed (%s, %s) — triggering self-healing...", by, value)
            healed = heal(self._driver, by, value, semantic_context or value)
            if healed:
                healed_by, healed_value = healed
                return self._driver.find_element(healed_by, healed_value)
            raise
        finally:
            self._driver.implicitly_wait(IMPLICIT_WAIT)

    def wait_and_find(self, by: str, value: str, semantic_context: str = "", timeout: int = EXPLICIT_WAIT):
        try:
            return WebDriverWait(self._driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except Exception:
            healed = heal(self._driver, by, value, semantic_context or value)
            if healed:
                healed_by, healed_value = healed
                return WebDriverWait(self._driver, timeout).until(
                    EC.element_to_be_clickable((healed_by, healed_value))
                )
            raise

    def get(self, url: str):
        self._driver.get(url)

    def quit(self):
        self._driver.quit()

    @property
    def title(self):
        return self._driver.title

    @property
    def current_url(self):
        return self._driver.current_url

    @property
    def page_source(self):
        return self._driver.page_source

    @property
    def driver(self):
        return self._driver