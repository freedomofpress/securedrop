#!/usr/bin/env python3

from glob import glob
from urllib.parse import urljoin

import os
import re
import requests
import sys

# Used to generate URLs for API endpoints and links; exposed as argument
from typing import List

from typing import Tuple

from typing import Dict

DEFAULT_BASE_URL = "https://weblate.securedrop.org"

# Where we look for screenshots: the page layout test results in English
SCREENSHOTS_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "tests/pageslayout/screenshots/en_US")
)

# What pattern we expect them to match
SCREENSHOTS_GLOB = "*.png"

# Regular expression rules that are applied sequentially to transform a
# filename into the canonical title we give that screenshot in Weblate.
#
# Example conversion: "source-session_timeout.png" -> "source: session timeout"
CANONICALIZATION_RULES = [(r"\.png$", ""), (r"-", ": "), (r"_", " ")]

# Weblate organizes internationalization work into projects and components,
# which are part of many URLs, and need to be referenced in some API requests.
PROJECT_SLUG = "securedrop"
COMPONENT_SLUG = "securedrop"

# Request limit for the number of pagination requests to issue before aborting.
REQUEST_LIMIT = 50


def main() -> None:
    """
    Uses the generic WeblateUploader class below to run a SecureDrop screenshot
    upload.
    """
    token = os.getenv("WEBLATE_API_TOKEN", None)
    base_url = os.getenv("WEBLATE_BASE_URL", DEFAULT_BASE_URL)

    if token is None:
        raise BadOrMissingTokenError(
            "No token provided via WEBLATE_API_TOKEN environment variable.", base_url
        )

    screenshot_files = glob(os.path.join(SCREENSHOTS_DIRECTORY, SCREENSHOTS_GLOB))
    if len(screenshot_files) == 0:
        print(
            "Page layout test results not found. Run this command from the SecureDrop"
        )
        print("base directory to generate the English language screenshots:\n")
        print("  LOCALES=en_US make translation-test")
        print("\nThis will take several minutes to complete.")
        sys.exit(1)

    uploader = WeblateUploader(
        token=token,
        base_url=base_url,
        project=PROJECT_SLUG,
        component=COMPONENT_SLUG,
        files=screenshot_files,
        request_limit=REQUEST_LIMIT,
        canonicalization_rules=CANONICALIZATION_RULES,
    )
    uploader.upload()


class WeblateUploader:
    """
    Manages Weblate screenshot batch uploads, matching filenames against
    titles of existing screenshots to create/update as appropriate.
    """

    def __init__(
        self,
        token: str,
        base_url: str,
        project: str,
        component: str,
        files: List[str],
        request_limit: int,
        canonicalization_rules: List[Tuple[str, str]],
    ) -> None:

        if len(token) != 40:
            raise BadOrMissingTokenError(
                "API token is not in expected 40 character format.", base_url
            )

        self.base_url = base_url
        self.screenshots_endpoint = urljoin(base_url, "/api/screenshots/")
        self.project = project
        self.component = component
        self.files = files
        self.request_limit = request_limit
        self.canonicalization_rules = canonicalization_rules
        self.user_agent = "Python Weblate Uploader V1.0"

        # While not all requests require authentication, any useful operation of this
        # script does, and providing a token for all requests ensures we avoid hitting
        # the rate limit for unauthenticated users. See:
        # https://docs.weblate.org/en/latest/api.html#rate-limiting
        self.session = requests.Session()
        headers = {
            "User-Agent": self.user_agent,
            "Authorization": "Token {}".format(token),
        }
        self.session.headers.update(headers)

    def get_existing_screenshots(self) -> List[Dict[str, str]]:
        """
        Obtains a list of all existing screenshots, and returns it as a list
        in the API's format. Paginates up to the request limit.
        """
        next_screenshots_url = self.screenshots_endpoint

        # API results are paginated, so we must loop through a set of results and
        # concatenate them.
        screenshots = []  # type: List[Dict[str, str]]
        request_count = 0
        while next_screenshots_url is not None:
            response = self.session.get(next_screenshots_url)
            response.raise_for_status()
            screenshots_page = response.json()
            next_screenshots_url = screenshots_page["next"]
            screenshots += screenshots_page["results"]
            request_count += 1
            if request_count >= self.request_limit:
                msg = "Request limit of {} exceeded. Aborting.".format(
                    self.request_limit
                )
                raise RequestLimitError(msg)
        return screenshots

    def _canonicalize(self, filename: str) -> str:
        """
        Derives a human-readable title from a filename using the defined
        canonicalization rules, if any. This is used to later update the
        screenshot.
        """
        for pattern, repl in self.canonicalization_rules:
            filename = re.sub(pattern, repl, filename)
        return filename

    def upload(self, check_existing_screenshots: bool = True) -> None:
        """
        Uploads all files using the screenshots endpoint. Optionally, checks
        files against a list of existing screenshots and replaces them rather
        than creating new uploads.
        """
        if check_existing_screenshots is True:
            existing_screenshots = self.get_existing_screenshots()
        else:
            existing_screenshots = []

        for file in self.files:
            basename = os.path.basename(file)
            canonical_name = self._canonicalize(basename)
            existing_screenshot_url = None

            for screenshot in existing_screenshots:
                if screenshot["name"] == canonical_name:
                    existing_screenshot_url = screenshot["file_url"]
                    break

            image = {"image": open(file, "rb")}

            if existing_screenshot_url is not None:
                print("Replacing existing screenshot {}".format(basename))
                response = self.session.post(existing_screenshot_url, files=image)
                response.raise_for_status()
            else:
                fields = {
                    "name": canonical_name,
                    "project_slug": "securedrop",
                    "component_slug": "securedrop",
                }
                print("Uploading new screenshot {}".format(basename))
                response = self.session.post(
                    self.screenshots_endpoint, files=image, data=fields
                )
                response.raise_for_status()

        result_url = urljoin(
            self.base_url, "screenshots/{}/{}".format(self.project, self.component)
        )
        print("Upload complete. Visit {} to review the results.".format(result_url))


class BadOrMissingTokenError(Exception):
    def __init__(self, reason: str, base_url: str) -> None:
        reason += " Obtain token via {}".format(
            urljoin(base_url, "accounts/profile/#api")
        )
        super().__init__(reason)


class RequestLimitError(Exception):
    pass


if __name__ == "__main__":
    main()
