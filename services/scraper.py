import os
import requests
from requests.auth import HTTPBasicAuth
import json
from typing import Any, Dict
from pydantic import HttpUrl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ticket(url: HttpUrl) -> str:
    """
    Use Selenium to scrape the text content of a Jira ticket given its URL.
    Returns the visible text content of the page.
    """
    # Get ChromeDriver path from environment variable
    driver_path = os.getenv("CHROMEDRIVER_PATH")
    if not driver_path:
        raise ValueError("CHROMEDRIVER_PATH is not set in environment")

    # Set up Chrome options for headless browsing
    options = Options()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1366,768")

    # Initialize the Chrome WebDriver service
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(str(url))

        # Debug helpers: save page_source and screenshot immediately
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("debug_screenshot.png")

        # Wait up to 15s for a known issue-content selector.
        # Common Jira selectors: issue-content, issue-view, or 'summary' headings.
        wait = WebDriverWait(driver, 15)
        possible_selectors = [
            (By.ID, "issue-content"),
            (By.CSS_SELECTOR, ".issue-body"),          # generic
            (By.CSS_SELECTOR, ".issue-layout"),        # new layouts
            (By.CSS_SELECTOR, "#summary-val"),         # older Jira
            (By.CSS_SELECTOR, ".issue-header-content"),# cloud-ish
            (By.TAG_NAME, "body"),
        ]

        element = None
        for by, sel in possible_selectors:
            try:
                element = wait.until(EC.presence_of_element_located((by, sel)))
                # If this selector returns something with visible text, break
                if element and element.text.strip():
                    break
            except Exception:
                element = None
                continue

        # If nothing matched with visible text, fall back to entire body
        if element is None:
            element = driver.find_element(By.TAG_NAME, "body")

        text_content = element.text.strip()
        # Save final page source & screenshot for debugging
        with open("debug_page_source_after_wait.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("debug_screenshot_after_wait.png")

        return text_content
    finally:
        # Ensure the driver is closed to free resources
        driver.quit()

def get_ticket(url: HttpUrl) -> Dict[str, Any]:
    # This code sample uses the 'requests' library:
    # http://docs.python-requests.org
    auth = HTTPBasicAuth("justinoghenekomeebedi@gmail.com", os.getenv("JIRA_API_KEY"))

    headers = {
    "Accept": "application/json"
    }

    response = requests.request(
    "GET",
    url,
    headers=headers,
    auth=auth
    )

    if response.status_code == 200:
        result = response.json()
        print('Result', json.dumps(result, sort_keys=True, indent=4))
        return result
    else:
        print('Error response: ', response.text or response.json())
