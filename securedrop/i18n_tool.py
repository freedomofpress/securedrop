#!/opt/venvs/securedrop-app-code/bin/python

import argparse
import glob
import json
import logging
import os
import re
import signal
import subprocess
import sys
import textwrap
from argparse import _SubParsersAction
from os.path import abspath, dirname, join, realpath
from pathlib import Path
from typing import Dict, List, Optional, Set

import version

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

I18N_CONF = os.path.join(os.path.dirname(__file__), "i18n.json")

# Map components of the "securedrop" Weblate project (keys) to their filesystem
# paths (values) relative to the repository root.
LOCALE_DIR = {
    "securedrop": "securedrop/translations",
    "desktop": "install_files/ansible-base/roles/tails-config/templates",
}


class I18NTool:
    #
    # The database of support language, indexed by the language code
    # used by weblate (i.e. whatever shows as CODE in
    # https://weblate.securedrop.org/projects/securedrop/securedrop/CODE/
    # is the index of the SUPPORTED_LANGUAGES database below.
    #
    # name: English name of the language to the documentation, not for
    #       display in the interface.
    # desktop: The language code used for desktop icons.
    #
    with open(I18N_CONF) as i18n_conf:
        conf = json.load(i18n_conf)
    supported_languages = conf["supported_locales"]
    release_tag_re = re.compile(r"^\d+\.\d+\.\d+$")
    translated_commit_re = re.compile("Translated using Weblate")
    updated_commit_re = re.compile(r"(?:updated from|  (?:revision|commit):) (\w+)")

    def file_is_modified(self, path: str) -> bool:
        return bool(subprocess.call(["git", "-C", dirname(path), "diff", "--quiet", path]))

    def ensure_i18n_remote(self, args: argparse.Namespace) -> None:
        """
        Make sure we have a git remote for the i18n repo.
        """

        k = {"cwd": args.root}
        if "i18n" not in subprocess.check_output(["git", "remote"], encoding="utf-8", **k):
            subprocess.check_call(["git", "remote", "add", "i18n", args.url], **k)
        subprocess.check_call(["git", "fetch", "i18n"], **k)

    def translate_messages(self, args: argparse.Namespace) -> None:
        messages_file = Path(args.translations_dir).absolute() / "messages.pot"

        if args.extract_update:
            if not os.path.exists(args.translations_dir):
                os.makedirs(args.translations_dir)
            sources = args.sources.split(",")
            subprocess.check_call(
                [
                    "pybabel",
                    "extract",
                    "--charset=utf-8",
                    "--mapping",
                    args.mapping,
                    "--output",
                    messages_file,
                    "--project=SecureDrop",
                    "--version",
                    args.version,
                    "--msgid-bugs-address=securedrop@freedom.press",
                    "--copyright-holder=Freedom of the Press Foundation",
                    "--add-comments=Translators:",
                    "--strip-comments",
                    "--add-location=never",
                    "--no-wrap",
                    *sources,
                ]
            )

            msg_file_content = messages_file.read_text()
            updated_content = _remove_from_content_line_with_text(
                text='"POT-Creation-Date:', content=msg_file_content
            )
            messages_file.write_text(updated_content)

            if (
                self.file_is_modified(str(messages_file))
                and len(os.listdir(args.translations_dir)) > 1
            ):
                tglob = f"{args.translations_dir}/*/LC_MESSAGES/*.po"
                for translation in glob.iglob(tglob):
                    subprocess.check_call(
                        [
                            "msgattrib",
                            "--no-fuzzy",
                            "--output-file",
                            translation,
                            translation,
                        ]
                    )
                    subprocess.check_call(
                        [
                            "msgmerge",
                            "--previous",
                            "--update",
                            "--no-fuzzy-matching",
                            "--no-wrap",
                            translation,
                            messages_file,
                        ]
                    )
                log.warning(f"messages translations updated in {messages_file}")
            else:
                log.warning("messages translations are already up to date")

        if args.compile and len(os.listdir(args.translations_dir)) > 1:
            # Suppress all pybabel to hide warnings (e.g.
            # https://github.com/python-babel/babel/issues/566) and verbose "compiling..." messages
            subprocess.run(
                ["pybabel", "compile", "--directory", args.translations_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def translate_desktop(self, args: argparse.Namespace) -> None:
        messages_file = Path(args.translations_dir).absolute() / "desktop.pot"

        if args.extract_update:
            sources = args.sources.split(",")

            # First extract from JavaScript sources via Babel ("xgettext
            # --language=JavaScript" can't parse gettext as exposed by GNOME
            # JavaScript):
            js_sources = [source for source in sources if ".js" in source]
            if js_sources:
                subprocess.check_call(
                    [
                        "pybabel",
                        "extract",
                        "--charset=utf-8",
                        "--mapping",
                        args.mapping,
                        "--output",
                        messages_file,
                        "--project=SecureDrop",
                        "--version",
                        args.version,
                        "--msgid-bugs-address=securedrop@freedom.press",
                        "--copyright-holder=Freedom of the Press Foundation",
                        "--add-comments=Translators:",
                        "--strip-comments",
                        "--add-location=never",
                        "--no-wrap",
                        *js_sources,
                    ],
                    cwd=args.translations_dir,
                )

            # Then extract from desktop templates via xgettext in appending
            # "--join-existing" mode:
            desktop_sources = [source for source in sources if ".js" not in source]
            subprocess.check_call(
                [
                    "xgettext",
                    "--join-existing",
                    f"--output={messages_file}",
                    "--language=Desktop",
                    "--keyword",
                    "--keyword=Name",
                    "--package-version",
                    args.version,
                    "--msgid-bugs-address=securedrop@freedom.press",
                    "--copyright-holder=Freedom of the Press Foundation",
                    *desktop_sources,
                ],
                cwd=args.translations_dir,
            )
            msg_file_content = messages_file.read_text()
            updated_content = _remove_from_content_line_with_text(
                text='"POT-Creation-Date:', content=msg_file_content
            )
            messages_file.write_text(updated_content)

            if self.file_is_modified(str(messages_file)):
                for f in os.listdir(args.translations_dir):
                    if not f.endswith(".po"):
                        continue
                    po_file = os.path.join(args.translations_dir, f)
                    subprocess.check_call(
                        ["msgmerge", "--no-fuzzy-matching", "--update", po_file, messages_file]
                    )
                log.warning(f"messages translations updated in {messages_file}")
            else:
                log.warning("desktop translations are already up to date")

        if args.compile:
            pos = [f for f in os.listdir(args.translations_dir) if f.endswith(".po")]
            linguas = [l[:-3] for l in pos]
            content = "\n".join(linguas) + "\n"
            linguas_file = join(args.translations_dir, "LINGUAS")
            try:
                open(linguas_file, "w").write(content)

                # First, compile each message catalog for normal gettext use.
                # We have to iterate over them, rather than using "pybabel
                # compile --directory", in order to replicate gettext's
                # standard "{locale}/LC_MESSAGES/{domain}.mo" structure (e.g.,
                # "securedrop/translations").
                locale_dir = os.path.join(args.translations_dir, "locale")
                for po in pos:
                    locale = po.replace(".po", "")
                    output_dir = os.path.join(locale_dir, locale, "LC_MESSAGES")
                    subprocess.run(["mkdir", "--parents", output_dir], check=True)
                    subprocess.run(
                        [
                            "msgfmt",
                            "--output-file",
                            os.path.join(output_dir, "messages.mo"),
                            po,
                        ],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        cwd=args.translations_dir,
                    )

                # Then use msgfmt to update the desktop files as usual.
                desktop_sources = [
                    source for source in args.sources.split(",") if ".js" not in source
                ]
                for source in desktop_sources:
                    target = source.rstrip(".in")
                    subprocess.check_call(
                        [
                            "msgfmt",
                            "--desktop",
                            "--template",
                            source,
                            "-o",
                            target,
                            "-d",
                            ".",
                        ],
                        cwd=args.translations_dir,
                    )
                    self.sort_desktop_template(join(args.translations_dir, target))
            finally:
                if os.path.exists(linguas_file):
                    os.unlink(linguas_file)

    def sort_desktop_template(self, template: str) -> None:
        """
        Sorts the lines containing the icon names.
        """
        lines = open(template).readlines()
        names = sorted(l for l in lines if l.startswith("Name"))
        others = (l for l in lines if not l.startswith("Name"))
        with open(template, "w") as new_template:
            for line in others:
                new_template.write(line)
            for line in names:
                new_template.write(line)

    def set_translate_parser(
        self, parser: argparse.ArgumentParser, translations_dir: str, sources: str
    ) -> None:
        parser.add_argument(
            "--extract-update",
            action="store_true",
            help=("extract strings to translate and " "update existing translations"),
        )
        parser.add_argument("--compile", action="store_true", help="compile translations")
        parser.add_argument(
            "--translations-dir",
            default=translations_dir,
            help=f"Base directory for translation files (default {translations_dir})",
        )
        parser.add_argument(
            "--version",
            default=version.__version__,
            help=(
                "SecureDrop version "
                "to store in pot files (default {})".format(version.__version__)
            ),
        )
        parser.add_argument(
            "--sources",
            default=sources,
            help=f"Source files and directories to extract (default {sources})",
        )

    def set_translate_messages_parser(self, subps: _SubParsersAction) -> None:
        parser = subps.add_parser(
            "translate-messages", help=("Update and compile " "source and template translations")
        )
        translations_dir = join(dirname(realpath(__file__)), "translations")
        sources = ".,source_templates,journalist_templates"
        self.set_translate_parser(parser, translations_dir, sources)
        mapping = "babel.cfg"
        parser.add_argument(
            "--mapping",
            default=mapping,
            help=f"Mapping of files to consider (default {mapping})",
        )
        parser.set_defaults(func=self.translate_messages)

    def set_translate_desktop_parser(self, subps: _SubParsersAction) -> None:
        parser = subps.add_parser(
            "translate-desktop", help=("Update and compile " "desktop icons translations")
        )
        translations_dir = join(
            dirname(realpath(__file__)),
            "..",
            LOCALE_DIR["desktop"],
        )
        sources = ",".join(
            [
                "desktop-journalist-icon.j2.in",
                "desktop-source-icon.j2.in",
                "extension.js.in",
            ]
        )
        mapping = join(dirname(realpath(__file__)), "babel.cfg")
        parser.add_argument(
            "--mapping",
            default=mapping,
            help=f"Mapping of files to consider (default {mapping})",
        )
        self.set_translate_parser(parser, translations_dir, sources)
        parser.set_defaults(func=self.translate_desktop)

    @staticmethod
    def require_git_email_name(git_dir: str) -> bool:
        cmd = (
            "git -C {d} config --get user.name > /dev/null && "
            "git -C {d} config --get user.email > /dev/null".format(d=git_dir)
        )
        # nosemgrep: python.lang.security.audit.subprocess-shell-true.subprocess-shell-true
        if subprocess.call(cmd, shell=True):  # nosec
            if "docker" in open("/proc/1/cgroup").read():
                log.error(
                    "remember ~/.gitconfig does not exist "
                    "in the dev-shell Docker container, "
                    "only .git/config does"
                )
            raise Exception(cmd + " returned false, please set name and email")
        return True

    def update_docs(self, args: argparse.Namespace) -> None:
        l10n_content = ".. GENERATED BY i18n_tool.py DO NOT EDIT:\n\n"
        for (code, info) in sorted(self.supported_languages.items()):
            l10n_content += "* " + info["name"] + " (``" + code + "``)\n"
        includes = abspath(join(args.docs_repo_dir, "docs/includes"))
        l10n_txt = join(includes, "l10n.txt")
        open(l10n_txt, mode="w").write(l10n_content)
        self.require_git_email_name(includes)
        if self.file_is_modified(l10n_txt):
            subprocess.check_call(["git", "add", "l10n.txt"], cwd=includes)
            msg = "docs: update the list of supported languages"
            subprocess.check_call(["git", "commit", "-m", msg, "l10n.txt"], cwd=includes)
            log.warning(l10n_txt + " updated")
            git_show_out = subprocess.check_output(["git", "show"], encoding="utf-8", cwd=includes)
            log.warning(git_show_out)
        else:
            log.warning(l10n_txt + " already up to date")

    def set_update_docs_parser(self, subps: _SubParsersAction) -> None:
        parser = subps.add_parser("update-docs", help=("Update the documentation"))
        parser.add_argument(
            "--docs-repo-dir",
            required=True,
            help=("root directory of the SecureDrop documentation repository"),
        )
        parser.set_defaults(func=self.update_docs)

    def update_from_weblate(self, args: argparse.Namespace) -> None:
        """
        Pull in updated translations from the i18n repo.
        """
        self.ensure_i18n_remote(args)

        # Check out *all* remote changes to the LOCALE_DIRs.
        subprocess.check_call(
            [
                "git",
                "checkout",
                args.target,
                "--",
                *LOCALE_DIR.values(),
            ],
            cwd=args.root,
        )

        # Use the LOCALE_DIR corresponding to the "securedrop" component to
        # determine which locales are present.
        locale_dir = os.path.join(args.root, LOCALE_DIR["securedrop"])
        locales = self.translated_locales(locale_dir)
        if args.supported_languages:
            codes = args.supported_languages.split(",")
            locales = {code: locales[code] for code in locales if code in codes}

        # Then iterate over all locales present and decide which to stage and commit.
        for code, path in locales.items():
            paths = []

            def add(path: str) -> None:
                """
                Add the file to the git index.
                """
                subprocess.check_call(["git", "add", path], cwd=args.root)
                paths.append(path)

            # Any translated locale may have changes that need to be staged from the
            # securedrop/securedrop component.
            add(path)

            # Only supported locales may have changes that need to be staged from the
            # securedrop/desktop component, because the link between the two components
            # is defined in I18N_CONF when a language is marked supported.
            try:
                info = self.supported_languages[code]
                name = info["name"]
                desktop_code = info["desktop"]
                path = join(
                    LOCALE_DIR["desktop"],
                    f"{desktop_code}.po",  # noqa: E741
                )
                add(path)
            except KeyError:
                log.info(
                    f"{code} has translations but is not marked as supported; "
                    f"skipping desktop translation"
                )
                name = code

            # Try to commit changes for this locale no matter what, even if it turns out to be a
            # no-op.
            self.commit_changes(args, code, name, paths)

    def translators(
        self, args: argparse.Namespace, path: str, since_commit: Optional[str]
    ) -> Set[str]:
        """
        Return the set of people who've modified a file in Weblate.

        Extracts all the authors of translation changes to the given
        path since the given commit. Translation changes are
        identified by the presence of "Translated using Weblate" in
        the commit message.
        """

        log_command = ["git", "--no-pager", "-C", args.root, "log", "--format=%aN\x1e%s\x1e%H"]

        if since_commit:
            since = self.get_commit_timestamp(args.root, since_commit)
            log_command.extend(["--since", since])

        log_command.extend([args.target, "--", path])

        # NB. We use an explicit str.split("\n") here because str.splitlines() splits on a
        # set of characters that includes the \x1e "record separator" we pass to "git log
        # --format" in log_command.  See #6648.
        log_lines = subprocess.check_output(log_command, encoding="utf-8").strip().split("\n")
        path_changes = [c.split("\x1e") for c in log_lines]
        path_changes = [
            c
            for c in path_changes
            if len(c) > 1 and c[2] != since_commit and self.translated_commit_re.match(c[1])
        ]
        log.debug("Path changes for %s: %s", path, path_changes)
        translators = {c[0] for c in path_changes}
        log.debug("Translators for %s: %s", path, translators)
        return translators

    def get_path_commits(self, root: str, path: str) -> List[str]:
        """
        Returns the list of commit hashes involving the path, most recent first.
        """
        cmd = ["git", "--no-pager", "log", "--format=%H", path]
        return subprocess.check_output(cmd, encoding="utf-8", cwd=root).splitlines()

    def translated_locales(self, path: str) -> Dict[str, str]:
        """Return a dictionary of all locale directories present in `path`, where the keys
        are the base (directory) names and the values are the full paths."""
        p = Path(path)
        return {x.name: str(x) for x in p.iterdir() if x.is_dir()}

    def commit_changes(
        self, args: argparse.Namespace, code: str, name: str, paths: List[str]
    ) -> None:
        """Check if any of the given paths have had changed staged.  If so, commit them."""
        self.require_git_email_name(args.root)
        authors = set()  # type: Set[str]
        cmd = ["git", "--no-pager", "diff", "--name-only", "--cached", *paths]
        diffs = subprocess.check_output(cmd, cwd=args.root, encoding="utf-8")

        # If nothing was changed, "git commit" will return nonzero as a no-op.
        if len(diffs) == 0:
            return

        # for each modified file, find the last commit made by this
        # function, then collect all the contributors since that
        # commit, so they can be credited in this one. if no commit
        # with the right message is found, just use the most recent
        # commit that touched the file.
        for path in paths:
            path_commits = self.get_path_commits(args.root, path)
            since_commit = None
            for path_commit in path_commits:
                commit_message = subprocess.check_output(
                    ["git", "--no-pager", "show", path_commit],
                    encoding="utf-8",
                    cwd=args.root,
                )
                m = self.updated_commit_re.search(commit_message)
                if m:
                    since_commit = m.group(1)
                    break
            log.debug("Crediting translators of %s since %s", path, since_commit)
            authors |= self.translators(args, path, since_commit)

        authors_as_str = "\n  ".join(sorted(authors))

        current = subprocess.check_output(
            ["git", "rev-parse", args.target], cwd=args.root, encoding="utf-8"
        )
        message = textwrap.dedent(
            """
        l10n: updated {name} ({code})

        contributors:
          {authors}

        updated from:
          repo: {remote}
          commit: {current}
        """
        ).format(remote=args.url, name=name, authors=authors_as_str, code=code, current=current)
        subprocess.check_call(["git", "commit", "-m", message, *paths], cwd=args.root)
        log.debug(f"Committing with this message: {message}")

    def set_update_from_weblate_parser(self, subps: _SubParsersAction) -> None:
        parser = subps.add_parser("update-from-weblate", help=("Import translations from weblate"))
        root = join(dirname(realpath(__file__)), "..")
        parser.add_argument(
            "--root",
            default=root,
            help=("root of the SecureDrop git repository" " (default {})".format(root)),
        )
        url = "https://github.com/freedomofpress/securedrop-i18n"
        parser.add_argument(
            "--url", default=url, help=("URL of the weblate repository" " (default {})".format(url))
        )
        parser.add_argument(
            "--target",
            default="i18n/i18n",
            help=(
                "Commit on i18n branch at which to stop gathering translator contributions "
                "(default: i18n/i18n)"
            ),
        )
        parser.add_argument(
            "--supported-languages", help="comma separated list of supported languages"
        )
        parser.set_defaults(func=self.update_from_weblate)

    def set_list_locales_parser(self, subps: _SubParsersAction) -> None:
        parser = subps.add_parser("list-locales", help="List supported locales")
        parser.add_argument(
            "--python",
            action="store_true",
            help=("Print the locales as a Python list suitable for config.py"),
        )
        parser.add_argument("--lines", action="store_true", help=("List one locale per line"))
        parser.set_defaults(func=self.list_locales)

    def list_locales(self, args: argparse.Namespace) -> None:
        if args.lines:
            for l in sorted(list(self.supported_languages.keys()) + ["en_US"]):
                print(l)
        elif args.python:
            print(sorted(list(self.supported_languages.keys()) + ["en_US"]))
        else:
            print(" ".join(sorted(list(self.supported_languages.keys()) + ["en_US"])))

    def set_list_translators_parser(self, subps: _SubParsersAction) -> None:
        parser = subps.add_parser("list-translators", help=("List contributing translators"))
        root = join(dirname(realpath(__file__)), "..")
        parser.add_argument(
            "--root",
            default=root,
            help=("root of the SecureDrop git repository" " (default {})".format(root)),
        )
        url = "https://github.com/freedomofpress/securedrop-i18n"
        parser.add_argument(
            "--url", default=url, help=("URL of the weblate repository" " (default {})".format(url))
        )
        parser.add_argument(
            "--target",
            default="i18n/i18n",
            help=(
                "Commit on i18n branch at which to stop gathering translator contributions "
                "(default: i18n/i18n)"
            ),
        )
        parser.add_argument(
            "--since",
            help=(
                "Gather translator contributions from the time of this commit "
                "(default: last release tag)"
            ),
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help=(
                "List everyone who's ever contributed, instead of just since the last "
                "release or specified commit."
            ),
        )
        parser.set_defaults(func=self.list_translators)

    def get_last_release(self, root: str) -> str:
        """
        Returns the last release tag, e.g. 1.5.0.
        """
        tags = (
            subprocess.check_output(["git", "-C", root, "tag", "--list"])
            .decode("utf-8")
            .splitlines()
        )
        release_tags = sorted([t.strip() for t in tags if self.release_tag_re.match(t)])
        if not release_tags:
            raise ValueError("Could not find a release tag!")
        return release_tags[-1]

    def get_commit_timestamp(self, root: str, commit: Optional[str]) -> str:
        """
        Returns the UNIX timestamp of the given commit.
        """
        cmd = ["git", "-C", root, "log", "-n", "1", "--pretty=format:%ct"]
        if commit:
            cmd.append(commit)

        timestamp = subprocess.check_output(cmd)
        return timestamp.decode("utf-8").strip()

    def list_translators(self, args: argparse.Namespace) -> None:
        self.ensure_i18n_remote(args)
        app_template = "{}/{}/LC_MESSAGES/messages.po"
        desktop_template = LOCALE_DIR["desktop"] + "/{}.po"
        since = None
        if args.all:
            print("Listing all translators who have ever helped")
        else:
            since = args.since if args.since else self.get_last_release(args.root)
            print(f"Listing translators who have helped since {since}")
        for code, info in sorted(self.supported_languages.items()):
            translators = set()
            paths = [
                app_template.format(LOCALE_DIR["securedrop"], code),
                desktop_template.format(info["desktop"]),
            ]
            for path in paths:
                try:
                    t = self.translators(args, path, since)
                    translators.update(t)
                except Exception as e:
                    print(f"Could not check git history of {path}: {e}", file=sys.stderr)
            print(
                "{} ({}):{}".format(
                    code,
                    info["name"],
                    "\n  {}\n".format("\n  ".join(sorted(translators))) if translators else "\n",
                )
            )

    def get_args(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=__file__, description="i18n tool for SecureDrop.")
        parser.set_defaults(func=lambda args: parser.print_help())

        parser.add_argument("-v", "--verbose", action="store_true")
        subps = parser.add_subparsers()

        self.set_translate_messages_parser(subps)
        self.set_translate_desktop_parser(subps)
        self.set_update_docs_parser(subps)
        self.set_update_from_weblate_parser(subps)
        self.set_list_translators_parser(subps)
        self.set_list_locales_parser(subps)

        return parser

    def setup_verbosity(self, args: argparse.Namespace) -> None:
        if args.verbose:
            logging.getLogger("sh.command").setLevel(logging.INFO)
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)

    def main(self, argv: List[str]) -> int:
        try:
            args = self.get_args().parse_args(argv)
            self.setup_verbosity(args)
            return args.func(args)
        except KeyboardInterrupt:
            return signal.SIGINT


def _remove_from_content_line_with_text(text: str, content: str) -> str:
    # Split where the text is located; assume there is only one instance of the text
    split_content = content.split(text)
    assert len(split_content) == 2

    # Remove the while line containing the text
    content_before_line = split_content[0]
    content_after_line = split_content[1].split("\n", maxsplit=1)[1]
    updated_content = content_before_line + content_after_line
    return updated_content


if __name__ == "__main__":  # pragma: no cover
    sys.exit(I18NTool().main(sys.argv[1:]))
