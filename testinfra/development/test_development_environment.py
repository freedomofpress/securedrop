import pytest
import getpass


def test_development_app_dependencies(Package):
    """
    Ensure development apt dependencies are installed.
    """
    development_apt_dependencies = [
      'libssl-dev',
      'ntp',
      'python-dev',
      'python-pip',
    ]
    for dependency in development_apt_dependencies:
        p = Package(dependency)
        assert p.is_installed


@pytest.mark.parametrize('pip_package,version', [
    ('Flask-Testing', '0.7.1'),
    ('Flask', '0.12.2'),
    ('Jinja2', '2.10'),
    ('MarkupSafe', '1.0'),
    ('Werkzeug', '0.12.2'),
    ('beautifulsoup4', '4.6.0'),
    ('click', '6.7'),
    ('coverage', '4.4.2'),
    ('first', '2.0.1'),
    ('funcsigs', '1.0.2'),
    ('itsdangerous', '0.24'),
    ('mock', '2.0.0'),
    ('pbr', '3.1.1'),
    ('pip-tools', '1.11.0'),
    ('py', '1.5.2'),
    ('pytest-cov', '2.5.1'),
    ('pytest', '3.3.2'),
    ('selenium', '2.53.6'),
    ('six', '1.11.0'),
])
def test_development_pip_dependencies(Command, Sudo, pip_package, version):
    """
    Declare SecureDrop app pip requirements. On the development VM,
    the pip dependencies should be installed directly via pip, rather
    than relying on the deb packages with pip-wheel inclusions.
    Versions here are intentionally hardcoded to track changes.
    """
    # Using elevated privileges to list the Python packages, since
    # the playbooks use sudo to install the pip packages system-wide.
    # In Travis, lack of sudo here hides a number of dependencies.
    with Sudo():
        c = Command('pip freeze')
        assert "{}=={}".format(pip_package, version) in c.stdout.rstrip()


@pytest.mark.skipif(getpass.getuser() != 'vagrant',
                    reason="vagrant bashrc checks dont make sense in CI")
def test_development_securedrop_env_var(File):
    """
    Ensure that the SECUREDROP_ENV var is set to "dev".


    TODO: this isn't really checking that the env var is set,
    just that it's declared in the bashrc. spec_helper ignores
    env vars via ssh by default, so start there.
    """

    f = File('/home/vagrant/.bashrc')
    assert f.is_file
    assert f.user == 'vagrant'
    assert f.contains('^export SECUREDROP_ENV=dev$')
