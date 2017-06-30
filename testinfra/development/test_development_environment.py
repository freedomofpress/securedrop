import pytest
import os
import getpass
import string

working_dir = os.path.dirname(os.path.realpath(__file__))
app_reqs_dir = os.path.realpath(os.path.join(working_dir,
                                             '../../securedrop/requirements'))

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

def create_reqs_list(file):
    """Parses a requirements.txt file in our app code requirements
    directory and returns a list of (dependency, version) tuples.
    """
    reqs = []
    with open(os.path.join(app_reqs_dir, file)) as fh:
        for line in fh:
            if line[0] in string.ascii_letters:
                name, version = line.rstrip('\n').split('==')
                name = name.lower()
                version = version.split(' ')[0]
                reqs.append((name, version))
    return reqs

@pytest.mark.parametrize('pip_package,version',
                         create_reqs_list('securedrop-requirements.txt'))
def test_development_pip_dependencies(Command, pip_package, version):
    """ Declare SecureDrop app pip requirements. On the development VM,
    the pip dependencies should be installed directly via pip, rather
    than relying on the deb packages with pip-wheel inclusions.
    """
    c = Command('pip freeze')
    assert "{}=={}".format(pip_package, version) in \
            c.stdout.rstrip().lower()

@pytest.mark.parametrize('pip_package,version',
                         create_reqs_list('test-requirements.txt'))
def test_development_pip_dependencies(Command, pip_package, version):
    """Declare SecureDrop app test pip requirements. These are only
    installed to the development VM. The `update_python_dependencies.py`
    utility in the SecureDrop root directory ensures these app and test
    requirements files do not conflict, so we can safely install both.
    This and the previous test together ensure this lack of conflict.
    """
    c = Command('pip freeze')
    assert "{}=={}".format(pip_package, version) in \
            c.stdout.rstrip().lower()

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
