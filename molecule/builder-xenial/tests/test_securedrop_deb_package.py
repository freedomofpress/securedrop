import pytest
import os
import re
import tempfile


SECUREDROP_TARGET_PLATFORM = os.environ.get("SECUREDROP_TARGET_PLATFORM")
testinfra_hosts = [
        "docker://{}-sd-dpkg-verification".format(SECUREDROP_TARGET_PLATFORM)
]
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
            config_version=securedrop_test_vars.config_version,
            grsec_version=securedrop_test_vars.grsec_version,
            securedrop_target_platform=securedrop_test_vars.securedrop_target_platform,
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
def test_build_deb_packages(host, deb):
    """
    Sanity check the built Debian packages for Control field
    values and general package structure.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    assert deb_package.is_file


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_packages_appear_installable(host, deb):
    """
    Confirms that a dry-run of installation reports no errors.
    Simple check for valid Debian package structure, but not thorough.
    When run on a malformed package, `dpkg` will report:

       dpkg-deb: error: `foo.deb' is not a debian format archive

    Testing application behavior is left to the functional tests.
    """

    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    deb_basename = os.path.basename(deb_package.path)
    package_name = extract_package_name_from_filepath(deb_package.path)
    assert deb_basename.startswith(package_name)

    # sudo is required to call `dpkg --install`, even as dry-run.
    with host.sudo():
        c = host.run("dpkg --install --dry-run {}".format(deb_package.path))
        assert "Selecting previously unselected package {}".format(
            package_name) in c.stdout
        regex = "Preparing to unpack [./]+{} ...".format(
            re.escape(deb_basename))
        assert re.search(regex, c.stdout, re.M)
        assert c.rc == 0


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_control_fields(host, deb):
    """
    Ensure Debian Control fields are populated as expected in the package.
    These checks are rather superficial, and don't actually confirm that the
    .deb files are not broken. At a later date, consider integration tests
    that actually use these built files during an Ansible provisioning run.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    package_name = extract_package_name_from_filepath(deb_package.path)
    # The `--field` option will display all fields if none are specified.
    c = host.run("dpkg-deb --field {}".format(deb_package.path))

    assert "Maintainer: SecureDrop Team <securedrop@freedom.press>" in c.stdout
    # The securedrop-config package is architecture indepedent
    if package_name == "securedrop-config":
        assert "Architecture: all" in c.stdout
    else:
        assert "Architecture: amd64" in c.stdout

    assert "Package: {}".format(package_name) in c.stdout
    assert c.rc == 0


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_control_fields_homepage(host, deb):
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    # The `--field` option will display all fields if none are specified.
    c = host.run("dpkg-deb --field {}".format(deb_package.path))
    # The OSSEC source packages will have a different homepage;
    # all other packages should set securedrop.org as homepage.
    if os.path.basename(deb_package.path).startswith('ossec-'):
        assert "Homepage: http://ossec.net" in c.stdout
    else:
        assert "Homepage: https://securedrop.org" in c.stdout


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_no_config_file(host, deb):
    """
    Ensures the `securedrop-app-code` package does not ship a `config.py`
    file. Doing so would clobber the site-specific changes made via Ansible.

    Somewhat lazily checking all deb packages, rather than just the app-code
    package, but it accomplishes the same in a DRY manner.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    c = host.run("dpkg-deb --contents {}".format(deb_package.path))
    assert not re.search("^.*/config\.py$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_pot_file(host, deb):
    """
    Ensures the `securedrop-app-code` package has the
    messages.pot file
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    c = host.run("dpkg-deb --contents {}".format(deb_package.path))
    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        assert re.search("^.*messages.pot$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_mo_file(host, deb):
    """
    Ensures the `securedrop-app-code` package has at least one
    compiled mo file.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    c = host.run("dpkg-deb --contents {}".format(deb_package.path))
    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        assert re.search("^.*messages\.mo$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_no_generated_assets(host, deb):
    """
    Ensures the `securedrop-app-code` package does not ship a minified
    static assets, which are built automatically via Flask-Assets, and may be
    present in the source directory used to build from.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))
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

        # no .map files should exist; only the generated CSS files.
        assert not re.search("^.*css.map$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_expected_conffiles(host, deb):
    """
    Ensures the `securedrop-app-code` package declares only whitelisted
    `conffiles`. Several files in `/etc/` would automatically be marked
    conffiles, which would break unattended updates to critical package
    functionality such as AppArmor profiles. This test validates overrides
    in the build logic to unset those conffiles.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    # For the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        tmpdir = tempfile.mkdtemp()
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
    if "securedrop-config" in deb_package.path:
        c = host.run("dpkg-deb -I {}".format(deb))
        assert "conffiles" not in c.stdout


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_package_contains_css(host, deb):
    """
    Ensures the `securedrop-app-code` package contains files that
    are generated during the `sass` build process.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))

        for css_type in ['journalist', 'source']:
            assert re.search("^.*\./var/www/securedrop/static/"
                             "css/{}.css$".format(css_type), c.stdout, re.M)


@pytest.mark.parametrize("deb, tag", deb_tags)
def test_deb_package_lintian(host, deb, tag):
    """
    Ensures lintian likes our  Debian packages.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    c = host.run("lintian --tags {} --no-tag-display-limit {}".format(
        tag, deb_package.path))
    assert len(c.stdout) == 0


@pytest.mark.parametrize("deb", deb_packages)
def test_deb_app_package_contains_https_validate_dir(host, deb):
    """
    Ensures the `securedrop-app-code` package ships with a validation
    '.well-known/pki-validation' directory
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))
        # well-known/pki-validation directory should exist
        assert re.search("^.*\./var/www/securedrop/"
                         ".well-known/pki-validation/$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_grsec_metapackage(host, deb):
    """
    Sanity checks on the securedrop-grsec metapackage. Mostly checks
    for presence of PaX flags hook and sysctl settings.
    Does not validate file contents, just presence.
    """

    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    if "securedrop-grsec" in deb_package.path:
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))
        # Custom sysctl options should be present
        assert re.search("^.*\./etc/sysctl.d/30-securedrop.conf$",
                         c.stdout, re.M)
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))
        # Post-install kernel hook for managing PaX flags must exist.
        assert re.search("^.*\./etc/kernel/postinst.d/paxctl-grub$",
                         c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_control_helper_files_are_present(host, deb):
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
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    # Only relevant for the securedrop-app-code package:
    if "securedrop-app-code" in deb_package.path:
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
        c = host.run("dpkg-deb --info {}".format(deb_package.path))
        for wanted_file in wanted_files:
            assert re.search("^\s+?\d+ bytes,\s+\d+ lines[\s*]+"+wanted_file+"\s+.*$",
                             c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_jinja_files_not_present(host, deb):
    """
    Make sure that jinja (.j2) files were not copied over
    as-is into the debian packages.
    """

    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))

    c = host.run("dpkg-deb --contents {}".format(deb_package.path))
    # There shouldn't be any files with a .j2 ending
    assert not re.search("^.*\.j2$", c.stdout, re.M)


@pytest.mark.parametrize("deb", deb_packages)
def test_ossec_binaries_are_present_agent(host, deb):
    """
    Inspect the package contents to ensure all ossec agent binaries are properly
    included in the package.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.ossec_version))
    # Only relevant for the ossec-agent package and not securedrop-ossec-agent:
    if "ossec-agent" in deb_package.path and "securedrop" not in deb_package.path:
        wanted_files = [
            "/var/ossec/bin/agent-auth",
            "/var/ossec/bin/ossec-syscheckd",
            "/var/ossec/bin/ossec-agentd",
            "/var/ossec/bin/manage_agents",
            "/var/ossec/bin/ossec-lua",
            "/var/ossec/bin/ossec-control",
            "/var/ossec/bin/ossec-luac",
            "/var/ossec/bin/ossec-logcollector",
            "/var/ossec/bin/util.sh",
            "/var/ossec/bin/ossec-execd",
        ]
        c = host.run("dpkg-deb -c {}".format(deb_package.path))
        for wanted_file in wanted_files:
            assert wanted_file in c.stdout


@pytest.mark.parametrize("deb", deb_packages)
def test_ossec_binaries_are_present_server(host, deb):
    """
    Inspect the package contents to ensure all ossec server binaries are properly
    included in the package.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.ossec_version))
    # Only relevant for the ossec-agent package and not securedrop-ossec-agent:
    if "ossec-server" in deb_package.path and "securedrop" not in deb_package.path:
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
            "/var/ossec/bin/ossec-lua",
            "/var/ossec/bin/rootcheck_control",
            "/var/ossec/bin/ossec-control",
            "/var/ossec/bin/ossec-dbd",
            "/var/ossec/bin/ossec-csyslogd",
            "/var/ossec/bin/ossec-regex",
            "/var/ossec/bin/ossec-luac",
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
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))
        for wanted_file in wanted_files:
            assert wanted_file in c.stdout


@pytest.mark.parametrize("deb", deb_packages)
def test_config_package_contains_expected_files(host, deb):
    """
    Inspect the package contents to ensure all config files are included in
    the package.
    """
    deb_package = host.file(deb.format(
        securedrop_test_vars.securedrop_version))
    if "securedrop-config" in deb_package.path:
        wanted_files = [
            "/etc/cron-apt/action.d/9-remove",
            "/etc/profile.d/securedrop_additions.sh",
        ]
        c = host.run("dpkg-deb --contents {}".format(deb_package.path))
        for wanted_file in wanted_files:
            assert wanted_file in c.stdout
