"""Youtube channel subscriber count screenshot."""

import sys
from io import BytesIO
from os import getenv
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# 頻道連結
CH_URI = "https://www.youtube.com/@RaimuMinto"

# 圖片大小
RAW_SCREENSHOT_HEIGHT = 188
TARGET_SCREENSHOT_WIDTH = 600

# 訂閱數暫存檔路徑
SUB_COUNT_PATH = Path("sub-count")

CHROME_PATH = getenv("CHROME_PATH")

if CHROME_PATH is None:
    msg = "CHROME_PATH is not set"
    raise ValueError(msg)

SETTINGS_LOCATOR = (By.XPATH, "//button[@aria-label='設定']")
CHANGE_THEME_LOCATOR = (By.TAG_NAME, "ytd-toggle-theme-compact-link-renderer")
DARK_THEME_LOCATOR = (By.XPATH, "//tp-yt-paper-item//yt-formatted-string[text()='深色主題']")
APP_LOCATOR = (By.TAG_NAME, "ytd-app")
CHANNEL_INFO_LOCATOR = (
    By.XPATH,
    "//span[contains(@class, 'yt-core-attributed-string yt-content-metadata-view-model-wiz__metadata-text')]",
)

options = webdriver.ChromeOptions()
options.binary_location = CHROME_PATH
options.add_argument("--headless")
options.add_argument("--disabled-dev-shm-usage")
options.add_argument("--lang=zh-TW")

driver = webdriver.Chrome(options=options)
driver.set_window_size(1920, 1080)


def _extract_number(text: str) -> str:
    for index, char in enumerate(text):
        if not char.isdigit():
            text = text[:index]
            break
    return text


def _extract_sub_count(text: str) -> str:
    if "." in text:
        digit, suffix = text.split(".", 1)
        suffix: str = _extract_number(suffix)
        sub_count: str = f"{digit}.{suffix}"
    else:
        sub_count = _extract_number(text)
    return sub_count


def get_page() -> None:
    """Get page."""
    driver.get(CH_URI)
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located((By.TAG_NAME, "ytd-app")))


def extract_sub_count() -> str:
    """Extract sub count from the page."""
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located(CHANNEL_INFO_LOCATOR))
    elements = driver.find_elements(*CHANNEL_INFO_LOCATOR)
    return next(_extract_sub_count(text) for element in elements if "訂閱者" in (text := element.text))


def set_dark_theme() -> None:
    """Set dark theme."""
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located(SETTINGS_LOCATOR))
    driver.find_element(*SETTINGS_LOCATOR).click()
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located(CHANGE_THEME_LOCATOR))
    driver.find_element(*CHANGE_THEME_LOCATOR).click()
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located(DARK_THEME_LOCATOR))
    driver.find_element(*DARK_THEME_LOCATOR).click()
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located(APP_LOCATOR))


if __name__ == "__main__":
    get_page()
    sub_count_now = extract_sub_count()

    if SUB_COUNT_PATH.exists() and sub_count_now == SUB_COUNT_PATH.read_text():
        sys.exit(0)

    SUB_COUNT_PATH.write_text(sub_count_now)
    set_dark_theme()
    screenshot: bytes = driver.find_element(By.TAG_NAME, "yt-page-header-renderer").screenshot_as_png
    driver.quit()

    Image.open(BytesIO(screenshot)).crop((0, 0, TARGET_SCREENSHOT_WIDTH, RAW_SCREENSHOT_HEIGHT)).save("screenshot.png")
