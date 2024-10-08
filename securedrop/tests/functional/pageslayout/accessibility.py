import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union

from selenium.webdriver.firefox.webdriver import WebDriver

_ACCESSIBILITY_DIR = (Path(__file__).parent / "accessibility-info").absolute()

_HTMLCS_RUNNER_CODE = """
var all_messages = [];
console.log = msg => {
    all_messages.push(msg);
};

HTMLCS_RUNNER.run('WCAG2AAA');
return all_messages;
"""


class MessageType(Enum):
    ERROR = 1
    WARNING = 2
    NOTICE = 3


@dataclass
class Message:
    """Contains all of the information in a message emitted by HTML CodeSniffer."""

    principle_id: str
    message: str
    message_type: MessageType
    responsible_html: str
    selector: str
    element_type: str

    @staticmethod
    def from_output(output: str) -> "Message":
        """Parses the output of htmlcs and returns an instance containing all data.

        No processing is performed for flexibility.

        Example message, post-split (note: contents of index 4 contains no newlines, but I had to
        split it to keep the linter happy):

        0: [HTMLCS] Error
        1: WCAG2AAA.Principle1.Guideline1_3.1_3_1_AAA.G141
        2: h2
        3: #security-level-heading
        4: The heading structure is not logically nested. This h2 element appears to be the
           primary document heading, so should be an h1 element.
        5: <h2 id="security-level-heading" hidden="">...</h2>
        """

        fields = output.split("|")

        if "Error" in fields[0]:
            message_type = MessageType.ERROR
        elif "Warning" in fields[0]:
            message_type = MessageType.WARNING
        elif "Notice" in fields[0]:
            message_type = MessageType.NOTICE
        else:
            raise ValueError(f"Unexpected message type: {fields[0]}")

        return Message(
            message_type=message_type,
            principle_id=fields[1],
            element_type=fields[2],
            selector=fields[3],
            message=fields[4],
            responsible_html=fields[5],
        )

    def __format__(self, _spec: str) -> str:
        newline = "\n"
        return f"""
{self.message_type}: {self.principle_id}
    {self.message}

    html:
        {self.responsible_html.replace(newline, f"{newline}        ")}
        """


def sniff_accessibility_issues(driver: WebDriver, locale: str, test_name: str) -> None:
    """Runs accessibility sniffs on the driver's current page.

    This function is responsible for injecting HTML CodeSniffer into the current page and writing
    the results to a file. This way, test functions can focus on the setup required to navigate to
    a particular URL (for example, logging in to get to the messages page).
    """

    # 1. Retrieve/compute required data
    with open("/usr/local/lib/node_modules/html_codesniffer/build/HTMLCS.js") as htmlcs:
        html_codesniffer = htmlcs.read()

    errors_dir = _ACCESSIBILITY_DIR / locale / "errors"
    errors_dir.mkdir(parents=True, exist_ok=True)

    reviews_dir = _ACCESSIBILITY_DIR / locale / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    # 2. Do the thing
    raw_messages = driver.execute_script(html_codesniffer + _HTMLCS_RUNNER_CODE)

    # 3. Organize the data
    messages: Dict[str, List[Message]] = {
        "machine-verified": [],
        "human-reviewed": [],
    }

    for message in map(Message.from_output, raw_messages[:-1]):  # last message is effectievly EOF
        if message.message_type == MessageType.ERROR:
            messages["machine-verified"].append(message)
        else:
            messages["human-reviewed"].append(message)

    # 4. Report the data
    # Note: it is useful to create empty files when there are no results to simplify the logic for
    #       summarizing the results, implemented in `summarize_accessibility_results`.
    with open(errors_dir / f"{test_name}.txt", "w") as error_file:
        for message in messages["machine-verified"]:
            error_file.write(f"{message}")

    with open(reviews_dir / f"{test_name}.txt", "w") as review_file:
        for message in messages["human-reviewed"]:
            review_file.write(f"{message}")


def summarize_accessibility_results() -> None:
    """Creates a file containing summary information about the result of accessiblity sniffing

    Note: This does not automatically run as part of the test suite, use
          `make accessibility-summary` instead.
    """

    try:
        summary: Dict[str, Dict[str, Dict[str, Union[int, bool]]]] = {}

        # since `sniff_accessibility_issues` creates empty files, all locale/type combinations will
        # contain the same set of files; getting filenames from en_US/reviews instead of, say,
        # ar/errors is arbitrary and sufficient
        for out_filename in os.listdir(_ACCESSIBILITY_DIR / "en_US" / "reviews"):
            summary[out_filename] = {
                "reviews": {"count": 0, "locale_differs": False},
                "errors": {"count": 0, "locale_differs": False},
            }

            # collect all of the relevant data
            for message_type in ["reviews", "errors"]:
                outputs: Dict[str, Dict[str, List[str]]] = {}

                for locale in ["en_US", "ar"]:
                    outputs[locale] = {}
                    with open(
                        _ACCESSIBILITY_DIR / locale / message_type / out_filename
                    ) as out_file:
                        # Only look at lines specifying the message (including the exact WCAG error
                        # code); this is exactly correct for the count, and approximately correct
                        # for comparing locales. If the order of the errors differs, or if there
                        # are a different number of any kind of error, this approximation will catch
                        # it.
                        outputs[locale][message_type] = [
                            line for line in out_file.readlines() if "MessageType." in line
                        ]

                summary[out_filename][message_type]["count"] = len(outputs["en_US"][message_type])
                summary[out_filename][message_type]["locale_differs"] = (
                    outputs["en_US"][message_type] != outputs["ar"][message_type]
                )

        # save the data to a convenient file
        with open(_ACCESSIBILITY_DIR / "summary.txt", "w") as summary_file:
            for name in sorted(summary.keys()):
                summary_file.write(name + ":\n")
                for message_type in ["errors", "reviews"]:
                    summary_file.write(
                        f"\t{message_type}: {summary[name][message_type]['count']}\n"
                    )
                    if summary[name][message_type]["locale_differs"]:
                        summary_file.write(f"\t        NOTE: {message_type} differ by locale\n")

                summary_file.write("\n")

    # this should only happen if the pageslayout tests have not created the raw output files
    except FileNotFoundError:
        print(
            f"ERROR: Run `make test TESTFILES={os.path.dirname(_ACCESSIBILITY_DIR)}` before "
            "running `make accessibility-summary`"
        )
