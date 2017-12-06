import pytest
import os
import re


securedrop_test_vars = pytest.securedrop_test_vars


def extract_package_name_from_filepath(filepath):
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
    package_name = re.search('^([a-z\-]+(?!\d))', deb_basename).groups()[0]
    assert deb_basename.startswith(package_name)
    return package_name


def get_deb_packages():
    """
    Helper function to retrieve module-namespace test vars and format
    the strings to interpolate version info. Keeps the test vars DRY
    in terms of version info, and required since we can't rely on
    Jinja-based evaluation of the YAML files (so we can't trivially
    reuse vars in other var values, as is the case with Ansible).
    """
    substitutions = dict(
            securedrop_version=securedrop_test_vars.securedrop_version,
            ossec_version=securedrop_test_vars.ossec_version,
            keyring_version=securedrop_test_vars.keyring_version,
            )

    deb_packages = [d.format(**substitutions) for d
                    in securedrop_test_vars.build_deb_packages]
    return deb_packages


deb_packages = get_deb_packages()


def get_deb_tags():
    """
    Helper function to build array of package and tag tuples
    for lintian.
    """
    deb_tags = []

    for deb in get_deb_packages():
        for tag in securedrop_test_vars.lintian_tags:
            deb_tags.append((deb, tag))

    return deb_tags


deb_tags = get_deb_tags()


@pytest.mark.parametrize("deb", deb_packages)
def test_build_deb_packages(File, deb):
    """
    Sanity check the built Debian packages for Control field
    values and general package structure.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    assert deb_package.is_file


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_packages_appear_installable(File, Command, Sudo, deb):
    """
    Confirms that a dry-run of installation reports no errors.
    Simple check for valid Debian package structure, but not thorough.
    When run on a malformed package, `dpkg` will report:

       dpkg-deb: error: `foo.deb' is not a debian format archive

    Testing application behavior is left to the functional tests.
    """

    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))

    deb_basename = os.path.basename(deb_package.path)
    package_name = extract_package_name_from_filepath(deb_package.path)
    assert deb_basename.startswith(package_name)

    # Sudo is required to call `dpkg --install`, even as dry-run.
    with Sudo():
        c = Command("dpkg --install --dry-run {}".format(deb_package.path))
        assert "Selecting previously unselected package {}".format(
            package_name) in c.stdout
        regex = "Preparing to unpack [./]+{} ...".format(
            re.escape(deb_basename))
        assert re.search(regex, c.stdout, re.M)
        assert c.rc == 0


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_control_fields(File, Command, deb):
    """
    Ensure Debian Control fields are populated as expected in the package.
    These checks are rather superficial, and don't actually confirm that the
    .deb files are not broken. At a later date, consider integration tests
    that actually use these built files during an Ansible provisioning run.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    package_name = extract_package_name_from_filepath(deb_package.path)
    # The `--field` option will display all fields if none are specified.
    c = Command("dpkg-deb --field {}".format(deb_package.path))

    assert "Maintainer: SecureDrop Team <securedrop@freedom.press>" in c.stdout
    assert "Architecture: amd64" in c.stdout
    assert "Package: {}".format(package_name) in c.stdout
    assert c.rc == 0


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_control_fields_homepage(File, Command, deb):
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    # The `--field` option will display all fields if none are specified.
    c = Command("dpkg-deb --field {}".format(deb_package.path))
    # The OSSEC source packages will have a different homepage;
    # all other packages should set securedrop.org as homepage.
    if os.path.basename(deb_package.path).startswith('ossec-'):
        assert "Homepage: http://ossec.net" in c.stdout
    else:
        assert "Homepage: https://securedrop.org" in c.stdout


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_no_config_file(File, Command, deb):
    """
    Ensures the `securedrop-app-code` package does not ship a `config.py`
    file. Doing so would clobber the site-specific changes made via Ansible.

    Somewhat lazily checking all deb packages, rather than just the app-code
    package, but it accomplishes the same in a DRY manner.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    c = Command("dpkg-deb --contents {}".format(deb_package.path))
    assert not re.search("^.*config\.py$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_pot_file(File, Command, deb):
    """
    Ensures the `securedrop-app-code` package has the
    messages.pot file
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    c = Command("dpkg-deb --contents {}".format(deb_package.path))
    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        assert re.search("^.*messages.pot$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_mo_file(File, Command, deb):
    """
    Ensures the `securedrop-app-code` package has at least one
    compiled mo file.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    c = Command("dpkg-deb --contents {}".format(deb_package.path))
    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        assert re.search("^.*messages\.mo$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_no_generated_assets(File, Command, deb):
    """
    Ensures the `securedrop-app-code` package does not ship a minified
    static assets, which are built automatically via Flask-Assets, and may be
    present in the source directory used to build from.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))

    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        c = Command("dpkg-deb --contents {}".format(deb_package.path))
        # static/gen/ directory should exist
        assert re.search("^.*\./var/www/securedrop"
                         "/static/gen/$", c.stdout, re.M)
        # static/gen/ directory should be empty
        assert not re.search("^.*\./var/www/securedrop"
                             "/static/gen/.+$", c.stdout, re.M)

        # static/.webassets-cache/ directory should exist
        assert re.search("^.*\./var/www/securedrop"
                         "/static/.webassets-cache/$", c.stdout, re.M)
        # static/.webassets-cache/ directory should be empty
        assert not re.search("^.*\./var/www/securedrop"
                             "/static/.webassets-cache/.+$", c.stdout, re.M)

        # no SASS files should exist; only the generated CSS files.
        assert not re.search("^.*sass.*$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_css(File, Command, deb):
    """
    Ensures the `securedrop-app-code` package contains files that
    are generated during the `sass` build process.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))

    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        c = Command("dpkg-deb --contents {}".format(deb_package.path))

        for css_type in ['journalist', 'source']:
            assert re.search("^.*\./var/www/securedrop/static/"
                             "css/{}.css$".format(css_type), c.stdout, re.M)
            assert re.search("^.*\./var/www/securedrop/static/"
                             "css/{}.css.map$".format(css_type), c.stdout,
                             re.M)


@pytest.mark.parametrize("deb, tag", deb_tags)
def test_deb_package_lintian(File, Command, deb, tag):
    """
    Ensures lintian likes our  Debian packages.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    c = Command("""lintian --tags {} --no-tag-display-limit {}""".format(
        tag, deb_package.path))
    assert len(c.stdout) == 0

@pytest.mark.parametrize("deb", deb_packages)
def test_deb_app_package_contains_https_validate_dir(host, deb):
    """
    Ensures the `securedrop-app-code` package ships with a validation
    '.well-known' directory
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))
        # static/gen/ directory should exist
        assert re.search("^.*\./var/www/securedrop/"
                ".well-known/$", c.stdout, re.M)
