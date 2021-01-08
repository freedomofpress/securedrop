import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple

import pytest
import yaml
from testinfra.host import Host


SECUREDROP_TARGET_PLATFORM = os.environ.get("SECUREDROP_TARGET_PLATFORM")
testinfra_hosts = [
    "docker://{}-sd-dpkg-verification".format(SECUREDROP_TARGET_PLATFORM)
]


def extract_package_name_from_filepath(filepath: str) -> str:
    """
    Helper function to infer intended package name from
    the absolute filepath, using a rather garish regex.
    E.g., given:
       securedrop-ossec-agent-2.8.2+0.3.10-amd64.deb

    retuns:

       securedrop-ossec-agent

    which can then be used for comparisons in dpkg output.
    """
    deb_basename = os.path.basename(filepath)
    package_match = re.search(r"^([a-z\-]+(?!\d))", deb_basename)
    assert package_match
    package_name = package_match.groups()[0]
    assert deb_basename.startswith(package_name)
    return package_name


def load_securedrop_test_vars() -> Dict[str, Any]:
    """
    Loads vars.yml into a dictionary.
    """
    filepath = os.path.join(os.path.dirname(__file__), "vars.yml")
    test_vars = yaml.safe_load(open(filepath))

    # Tack on target OS for use in tests
    test_vars["securedrop_target_platform"] = os.environ.get(
        "SECUREDROP_TARGET_PLATFORM"
    )

    return test_vars


securedrop_test_vars = load_securedrop_test_vars()


def make_deb_paths() -> Dict[str, Path]:
    """
    Helper function to retrieve module-namespace test vars and format
    the strings to interpolate version info. Keeps the test vars DRY
    in terms of version info, and required since we can't rely on
    Jinja-based evaluation of the YAML files (so we can't trivially
    reuse vars in other var values, as is the case with Ansible).
    """
    grsec_version = securedrop_test_vars["grsec_version"]
    if SECUREDROP_TARGET_PLATFORM == "focal":
        grsec_version = grsec_version+"+focal"

    substitutions = dict(
        securedrop_version=securedrop_test_vars["securedrop_version"],
        ossec_version=securedrop_test_vars["ossec_version"],
        keyring_version=securedrop_test_vars["keyring_version"],
        config_version=securedrop_test_vars["config_version"],
        grsec_version=grsec_version,
        securedrop_target_platform=securedrop_test_vars["securedrop_target_platform"],
    )

    return {
        package_name: Path(path.format(**substitutions))
        for package_name, path in securedrop_test_vars["deb_paths"].items()
    }


deb_paths = make_deb_paths()


@pytest.fixture(scope="module")
def securedrop_app_code_contents(host) -> str:
    """
    Returns the content listing of the securedrop-app-code Debian package on the host.
    """
    return host.run("dpkg-deb --contents {}".format(deb_paths["securedrop_app_code"])).stdout


def deb_tags() -> List[Tuple[Path, str]]:
    """
    Helper function to build array of package and tag tuples
    for lintian.
    """
    tags = []

    for deb in deb_paths.values():
        for tag in securedrop_test_vars["lintian_tags"]:
            tags.append((deb, tag))

    return tags


def get_source_paths(
    starting_path: Path,
    pattern: str = "**/*",
    skip: Optional[List[Pattern]] = None,
) -> List[Path]:
    """
    Returns paths under starting_path that match the given pattern.

    The starting_path argument specifies where to look for files. The
    optional pattern and skip parameters can be used to filter the
    results.
    """
    paths = sorted(p for p in starting_path.glob(pattern))
    if skip:
        paths = [p for p in paths if not any(s.search(str(p)) for s in skip)]
    assert paths
    return paths


def get_static_asset_paths(securedrop_root: Path, pattern: str) -> List[Path]:
    """
    Returns static assets matching the pattern.
    """
    static_dir = securedrop_root / "securedrop/static"
    skip = [
        re.compile(p) for p in [r"\.map$", r"\.webassets-cache$", "custom_logo.png$"]
    ]
    return get_source_paths(static_dir, pattern, skip)


def verify_static_assets(
    securedrop_app_code_contents: str, securedrop_root: Path, pattern
) -> None:
    """
    Verifies that the securedrop-app-code package contains the given static assets.

    Example: verify_assets(securedrop_app_code_contents, "icons/**.png")
    """
    for asset_path in get_static_asset_paths(securedrop_root, pattern):
        assert re.search(
            r"^.*\./var/www/" "{}$".format(asset_path.relative_to(securedrop_root)),
            securedrop_app_code_contents,
            re.M,
        )


@pytest.mark.parametrize("deb", deb_paths.values())
def test_build_deb_packages(host: Host, deb: Path) -> None:
    """
    Sanity check the built Debian packages for Control field
    values and general package structure.
    """
    deb_package = host.file(str(deb))
    assert deb_package.is_file


@pytest.mark.parametrize("deb", deb_paths.values())
def test_deb_packages_appear_installable(host: Host, deb: Path) -> None:
    """
    Confirms that a dry-run of installation reports no errors.
    Simple check for valid Debian package structure, but not thorough.
    When run on a malformed package, `dpkg` will report:

       dpkg-deb: error: `foo.deb' is not a debian format archive

    Testing application behavior is left to the functional tests.
    """

    package_name = extract_package_name_from_filepath(str(deb))
    assert deb.name.startswith(package_name)

    # sudo is required to call `dpkg --install`, even as dry-run.
    with host.sudo():
        c = host.run("dpkg --install --dry-run {}".format(deb))
        assert (
            "Selecting previously unselected package {}".format(package_name)
            in c.stdout
        )
        regex = "Preparing to unpack [./]+{} ...".format(re.escape(deb.name))
        assert re.search(regex, c.stdout, re.M)
        assert c.rc == 0


@pytest.mark.parametrize("deb", deb_paths.values())
def test_deb_package_control_fields(host: Host, deb: Path) -> None:
    """
    Ensure Debian Control fields are populated as expected in the package.
    These checks are rather superficial, and don't actually confirm that the
    .deb files are not broken. At a later date, consider integration tests
    that actually use these built files during an Ansible provisioning run.
    """
    package_name = extract_package_name_from_filepath(str(deb))
    # The `--field` option will display all fields if none are specified.
    c = host.run("dpkg-deb --field {}".format(deb))

    assert "Maintainer: SecureDrop Team <securedrop@freedom.press>" in c.stdout
    # The securedrop-config package is architecture indepedent
    if package_name == "securedrop-config":
        assert "Architecture: all" in c.stdout
    else:
        assert "Architecture: amd64" in c.stdout

    assert "Package: {}".format(package_name) in c.stdout
    assert c.rc == 0


@pytest.mark.parametrize("deb", deb_paths.values())
def test_deb_package_control_fields_homepage(host: Host, deb: Path):
    # The `--field` option will display all fields if none are specified.
    c = host.run("dpkg-deb --field {}".format(deb))
    # The OSSEC source packages will have a different homepage;
    # all other packages should set securedrop.org as homepage.
    if deb.name.startswith("ossec-"):
        assert "Homepage: http://ossec.net" in c.stdout
    else:
        assert "Homepage: https://securedrop.org" in c.stdout


def test_securedrop_app_code_contains_no_config_file(securedrop_app_code_contents: str):
    """
    Ensures the `securedrop-app-code` package does not ship a `config.py`
    file. Doing so would clobber the site-specific changes made via Ansible.
    """
    assert not re.search(
        r"^ ./var/www/securedrop/config.py$", securedrop_app_code_contents, re.M
    )


def test_securedrop_app_code_contains_pot_file(securedrop_app_code_contents: str):
    """
    Ensures the `securedrop-app-code` package has the
    messages.pot file
    """
    assert re.search(
        "^.* ./var/www/securedrop/translations/messages.pot$",
        securedrop_app_code_contents,
        re.M,
    )


def test_securedrop_app_code_contains_mo_files(
    securedrop_root: Path, securedrop_app_code_contents: str
) -> None:
    """
    Ensures the `securedrop-app-code` package has a compiled version of each .po file.
    """
    po_paths = get_source_paths(securedrop_root / "securedrop/translations", "**/*.po")
    mo_paths = [p.with_suffix(".mo") for p in po_paths]
    for mo in mo_paths:
        assert re.search(
            r"^.* \./var/www/" "{}$".format(mo.relative_to(securedrop_root)),
            securedrop_app_code_contents,
            re.M,
        )


def test_deb_package_contains_no_generated_assets(securedrop_app_code_contents: str):
    """
    Ensures the `securedrop-app-code` package does not ship minified
    static assets, which are built automatically via Flask-Assets, and
    may be present in the source directory used to build from.
    """
    # static/gen/ directory should exist
    assert re.search(
        r"^.*\./var/www/securedrop" "/static/gen/$", securedrop_app_code_contents, re.M
    )
    # static/gen/ directory should be empty
    assert not re.search(
        r"^.*\./var/www/securedrop" "/static/gen/.+$",
        securedrop_app_code_contents,
        re.M,
    )

    # static/.webassets-cache/ directory should exist
    assert re.search(
        r"^.*\./var/www/securedrop" "/static/.webassets-cache/$",
        securedrop_app_code_contents,
        re.M,
    )
    # static/.webassets-cache/ directory should be empty
    assert not re.search(
        r"^.*\./var/www/securedrop" "/static/.webassets-cache/.+$",
        securedrop_app_code_contents,
        re.M,
    )

    # no SASS files should exist; only the generated CSS files.
    assert not re.search("^.*sass$", securedrop_app_code_contents, re.M)

    # no .map files should exist; only the generated CSS files.
    assert not re.search("^.*css.map$", securedrop_app_code_contents, re.M)


@pytest.mark.parametrize("deb", deb_paths.values())
def test_deb_package_contains_expected_conffiles(host: Host, deb: Path):
    """
    Ensures the `securedrop-app-code` package declares only whitelisted
    `conffiles`. Several files in `/etc/` would automatically be marked
    conffiles, which would break unattended updates to critical package
    functionality such as AppArmor profiles. This test validates overrides
    in the build logic to unset those conffiles.
    """
    # For the securedrop-app-code package:
    if deb.name.startswith("securedrop-app-code"):
        mktemp = host.run("mktemp -d")
        tmpdir = mktemp.stdout.strip()
        # The `--raw-extract` flag includes `DEBIAN/` dir with control files
        host.run("dpkg-deb --raw-extract {} {}".format(deb, tmpdir))
        conffiles_path = os.path.join(tmpdir, "DEBIAN", "conffiles")
        f = host.file(conffiles_path)

        assert f.is_file
        # Ensure that the entirety of the file lists only the logo as conffile;
        # effectively ensures e.g. AppArmor profiles are not conffiles.
        conffiles = f.content_string.rstrip()
        assert conffiles == "/var/www/securedrop/static/i/logo.png"

    # For the securedrop-config package, we want to ensure there are no
    # conffiles so securedrop_additions.sh is squashed every time
    if deb.name.startswith("securedrop-config"):
        c = host.run("dpkg-deb -I {}".format(deb))
        assert "conffiles" not in c.stdout


def test_securedrop_app_code_contains_css(securedrop_app_code_contents: str) -> None:
    """
    Ensures the `securedrop-app-code` package contains files that
    are generated during the `sass` build process.
    """
    for css_type in ["journalist", "source"]:
        assert re.search(
            r"^.*\./var/www/securedrop/static/" "css/{}.css$".format(css_type),
            securedrop_app_code_contents,
            re.M,
        )


def test_securedrop_app_code_contains_static_fonts(
    securedrop_root: Path, securedrop_app_code_contents: str
):
    """
    Ensures the `securedrop-app-code` package contains everything under securedrop/fonts.
    """
    verify_static_assets(securedrop_app_code_contents, securedrop_root, "fonts/*.*")


def test_securedrop_app_code_contains_static_i(
    securedrop_root: Path, securedrop_app_code_contents: str
):
    """
    Ensures the `securedrop-app-code` package contains everything under securedrop/static/i.
    """
    verify_static_assets(securedrop_app_code_contents, securedrop_root, "i/**/*.*")


def test_securedrop_app_code_contains_static_icons(
    securedrop_root: Path, securedrop_app_code_contents: str
):
    """
    Ensures the `securedrop-app-code` package contains all the icons.
    """
    verify_static_assets(securedrop_app_code_contents, securedrop_root, "icons/*.png")


def test_securedrop_app_code_contains_static_javascript(
    securedrop_root: Path, securedrop_app_code_contents: str
):
    """
    Ensures the `securedrop-app-code` package contains all the JavaScript.
    """
    verify_static_assets(securedrop_app_code_contents, securedrop_root, "js/*.js")


@pytest.mark.parametrize("deb, tag", deb_tags())
def test_deb_package_lintian(host: Host, deb: Path, tag: str):
    """
    Ensures lintian likes our Debian packages.
    """
    c = host.run("lintian --tags {} --no-tag-display-limit {}".format(tag, deb))
    assert len(c.stdout) == 0


def test_deb_app_package_contains_https_validate_dir(securedrop_app_code_contents: str):
    """
    Ensures the `securedrop-app-code` package ships with a validation
    '.well-known/pki-validation' directory
    """
    # well-known/pki-validation directory should exist
    assert re.search(
        r"^.*\./var/www/securedrop/" ".well-known/pki-validation/$",
        securedrop_app_code_contents,
        re.M,
    )


def test_grsec_metapackage(host: Host):
    """
    Sanity checks on the securedrop-grsec metapackage. Mostly checks
    for presence of PaX flags hook and sysctl settings.
    Does not validate file contents, just presence.
    """

    c = host.run("dpkg-deb --contents {}".format(deb_paths["securedrop_grsec"]))
    contents = c.stdout
    if SECUREDROP_TARGET_PLATFORM == "xenial":
        # Post-install kernel hook for managing PaX flags must exist.
        assert re.search(r"^.*\./etc/kernel/postinst.d/paxctl-grub$", contents, re.M)
        # Config file for paxctld should not be present
        assert not re.search(r"^.*\./opt/securedrop/paxctld.conf$", contents, re.M)
    else:
        assert not re.search(r"^.*\./etc/kernel/postinst.d/paxctl-grub$", contents, re.M)
        assert re.search(r"^.*\./opt/securedrop/paxctld.conf$", contents, re.M)

    # Custom sysctl options should be present
    assert re.search(r"^.*\./etc/sysctl.d/30-securedrop.conf$", contents, re.M)


def test_control_helper_files_are_present(host: Host):
    """
    Inspect the package info to get a list of helper scripts
    that should be shipped with the package, e.g. postinst, prerm, etc.
    Necessary due to package build logic retooling.

    Example output from package info, for reference:

      $ dpkg-deb --info securedrop-app-code_0.12.0~rc1_amd64.deb
      new debian package, version 2.0.
      size 13583186 bytes: control archive=11713 bytes.
           62 bytes,     2 lines      conffiles
          657 bytes,    10 lines      control
        26076 bytes,   298 lines      md5sums
         5503 bytes,   159 lines   *  postinst             #!/bin/bash

    Note that the actual output will have trailing whitespace, removed
    from this text description to satisfy linters.
    """
    wanted_files = [
        "conffiles",
        "config",
        "control",
        "postinst",
        "postrm",
        "preinst",
        "prerm",
        "templates",
    ]
    c = host.run("dpkg-deb --info {}".format(deb_paths["securedrop_app_code"]))
    for wanted_file in wanted_files:
        assert re.search(
            r"^\s+?\d+ bytes,\s+\d+ lines[\s*]+" + wanted_file + r"\s+.*$",
            c.stdout,
            re.M,
        )


@pytest.mark.parametrize("deb", deb_paths.values())
def test_jinja_files_not_present(host: Host, deb: Path):
    """
    Make sure that jinja (.j2) files were not copied over
    as-is into the debian packages.
    """

    c = host.run("dpkg-deb --contents {}".format(deb))
    # There shouldn't be any files with a .j2 ending
    assert not re.search(r"^.*\.j2$", c.stdout, re.M)


def test_ossec_binaries_are_present_agent(host: Host):
    """
    Inspect the package contents to ensure all ossec agent binaries are properly
    included in the package.
    """
    wanted_files = [
        "/var/ossec/bin/agent-auth",
        "/var/ossec/bin/ossec-syscheckd",
        "/var/ossec/bin/ossec-agentd",
        "/var/ossec/bin/manage_agents",
        "/var/ossec/bin/ossec-control",
        "/var/ossec/bin/ossec-logcollector",
        "/var/ossec/bin/util.sh",
        "/var/ossec/bin/ossec-execd",
    ]
    c = host.run("dpkg-deb -c {}".format(deb_paths["ossec_agent"]))
    for wanted_file in wanted_files:
        assert re.search(
            r"^.* .{}$".format(wanted_file),
            c.stdout,
            re.M,
        )


def test_ossec_binaries_are_present_server(host: Host):
    """
    Inspect the package contents to ensure all ossec server binaries are properly
    included in the package.
    """
    wanted_files = [
        "/var/ossec/bin/ossec-maild",
        "/var/ossec/bin/ossec-remoted",
        "/var/ossec/bin/ossec-syscheckd",
        "/var/ossec/bin/ossec-makelists",
        "/var/ossec/bin/ossec-logtest",
        "/var/ossec/bin/syscheck_update",
        "/var/ossec/bin/ossec-reportd",
        "/var/ossec/bin/ossec-agentlessd",
        "/var/ossec/bin/manage_agents",
        "/var/ossec/bin/rootcheck_control",
        "/var/ossec/bin/ossec-control",
        "/var/ossec/bin/ossec-dbd",
        "/var/ossec/bin/ossec-csyslogd",
        "/var/ossec/bin/ossec-regex",
        "/var/ossec/bin/agent_control",
        "/var/ossec/bin/ossec-monitord",
        "/var/ossec/bin/clear_stats",
        "/var/ossec/bin/ossec-logcollector",
        "/var/ossec/bin/list_agents",
        "/var/ossec/bin/verify-agent-conf",
        "/var/ossec/bin/syscheck_control",
        "/var/ossec/bin/util.sh",
        "/var/ossec/bin/ossec-analysisd",
        "/var/ossec/bin/ossec-execd",
        "/var/ossec/bin/ossec-authd",
    ]
    c = host.run("dpkg-deb --contents {}".format(deb_paths["ossec_server"]))
    for wanted_file in wanted_files:
        assert re.search(
            r"^.* .{}$".format(wanted_file),
            c.stdout,
            re.M,
        )


def test_config_package_contains_expected_files(host: Host) -> None:
    """
    Inspect the package contents to ensure all config files are included in
    the package.
    """
    wanted_files = [
        "/etc/cron-apt/action.d/9-remove",
        "/etc/profile.d/securedrop_additions.sh",
    ]
    c = host.run("dpkg-deb --contents {}".format(deb_paths["securedrop_config"]))
    for wanted_file in wanted_files:
        assert re.search(
            r"^.* .{}$".format(wanted_file),
            c.stdout,
            re.M,
        )


def test_app_package_does_not_contain_custom_logo(
    securedrop_app_code_contents: str,
) -> None:
    """
    Inspect the package contents to ensure custom_logo.png is not present. This
    is because custom_logo.png superceeds logo.png.
    """
    assert "/var/www/static/i/custom_logo.png" not in securedrop_app_code_contents
