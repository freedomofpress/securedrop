import os
from io import BytesIO
from pathlib import Path
from typing import List

from PIL import Image
from selenium.webdriver.firefox.webdriver import WebDriver

_SCREENSHOTS_DIR = (Path(__file__).parent / "screenshots").absolute()
_HTML_DIR = (Path(__file__).parent / "html").absolute()


def save_screenshot_and_html(driver: WebDriver, locale: str, test_name: str) -> None:
    # Save a screenshot
    locale_screenshot_dir = _SCREENSHOTS_DIR / locale
    locale_screenshot_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(BytesIO(driver.get_screenshot_as_png()))
    cropped = _autocrop_btm(img)
    cropped.save(str(locale_screenshot_dir / f"{test_name}.png"))

    # Save the HTML content
    locale_html_dir = _HTML_DIR / locale
    locale_html_dir.mkdir(parents=True, exist_ok=True)

    html = driver.page_source
    (locale_html_dir / f"{test_name}.html").write_text(html)


def _autocrop_btm(img, bottom_padding=12):
    """Automatically crop the bottom of a screenshot."""
    # Get the grayscale of img
    gray = img.convert("L")
    # We start one row above the bottom since the "modal" windows screenshots
    # have a bottom line color different than the background
    btm = img.height - 2
    # Get the background luminance value from the bottom-leftmost pixel
    bg = gray.getpixel((0, btm))

    # Move up until the full row is not of the background luminance
    while btm > 0 and all([gray.getpixel((col, btm)) == bg for col in range(gray.width)]):
        btm -= 1

    btm = min(btm + bottom_padding, img.height)

    return img.crop((0, 0, img.width, btm))


def list_locales() -> List[str]:
    if "TEST_LOCALES" in os.environ:
        locales = os.environ["TEST_LOCALES"].split()
    else:
        locales = ["en_US"]
    return locales
