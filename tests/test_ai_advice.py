# import os
# import time
# import pytest
# import logging
#
# from selenium.common.exceptions import NoAlertPresentException
# from core.driver import SelfHealingDriver
# from pages.dashboard_page import DashboardPage
#
# logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
# logger = logging.getLogger(__name__)
#
# HTML_FILE = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "..", "aimanager.html")
# )
#
# @pytest.fixture(scope="module")
# def page_with_data():
#     driver = SelfHealingDriver()
#     dp = DashboardPage(driver)
#     dp.open(HTML_FILE)
#     dp.add_entry("2025-03-01", "profit", 8000, "Product sales")
#     dp.add_entry("2025-03-05", "loss", 2000, "Marketing spend")
#     dp.add_entry("2025-03-10", "profit", 5500, "Consulting fee")
#     yield dp
#     driver.quit()
#
# @pytest.fixture(scope="module")
# def empty_page():
#     driver = SelfHealingDriver()
#     dp = DashboardPage(driver)
#     dp.open(HTML_FILE)
#     yield dp
#     driver.quit()
#
# class TestAIAdvice:
#
#     def test_advice_button_exists(self, page_with_data):
#         text = page_with_data.get_ai_output_text()
#         assert text is not None
#
#     def test_advice_button_clickable_with_no_data(self, empty_page):
#         empty_page.click_get_advice()
#         time.sleep(0.5)
#         try:
#             alert = empty_page._d.driver.switch_to.alert
#             alert_text = alert.text
#             alert.accept()
#             assert "data" in alert_text.lower() or "add" in alert_text.lower()
#         except NoAlertPresentException:
#             pass
#
#     def test_advice_output_changes_after_click(self, page_with_data):
#         initial_text = page_with_data.get_ai_output_text()
#         page_with_data.click_get_advice()
#         for _ in range(40):
#             time.sleep(0.5)
#             current = page_with_data.get_ai_output_text()
#             if current != initial_text and "Thinking" not in current:
#                 break
#         final_text = page_with_data.get_ai_output_text()
#         assert final_text != initial_text
#
#     def test_advice_output_not_empty(self, page_with_data):
#         text = page_with_data.get_ai_output_text()
#         assert len(text.strip()) > 20
#
#     def test_advice_output_not_error(self, page_with_data):
#         text = page_with_data.get_ai_output_text().lower()
#         assert "api error" not in text