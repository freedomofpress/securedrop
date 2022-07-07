from io import BytesIO
from pathlib import Path

from PIL import Image
from selenium.webdriver.firefox.webdriver import WebDriver
from tests.functional.pageslayout.functional_test import autocrop_btm

_SCREENSHOTS_DIR = (Path(__file__).parent / "screenshots").absolute()
_HTML_DIR = (Path(__file__).parent / "html").absolute()


# TODO(AD): This intends to replace FunctionalTest._screenshot() and _html()
def save_screenshot_and_html(driver: WebDriver, locale: str, test_name: str) -> None:
    # Save a screenshot
    locale_screenshot_dir = _SCREENSHOTS_DIR / locale
    locale_screenshot_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(BytesIO(driver.get_screenshot_as_png()))
    cropped = autocrop_btm(img)
    cropped.save(str(locale_screenshot_dir / f"{test_name}.png"))

    # Save the HTML content
    locale_html_dir = _HTML_DIR / locale
    locale_html_dir.mkdir(parents=True, exist_ok=True)

    html = driver.page_source
    (locale_html_dir / f"{test_name}.html").write_text(html)
