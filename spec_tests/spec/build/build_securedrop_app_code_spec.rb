# declare filenames for built debs
deb_filepath = "/tmp/securedrop-app-code-#{property['securedrop_app_code_version']}-amd64.deb"
deb_apt_dependencies = %w(
  python-pip
  apparmor-utils
  gnupg2
  haveged
  python
  python-pip
  secure-delete
  sqlite
  apache2-mpm-worker
  libapache2-mod-wsgi
  libapache2-mod-xsendfile
  redis-server
  supervisor
)

# ensure required debs exist
describe file(deb_filepath) do
  it { should be_file }
end

# get file basename of package, stripping leading dirs
deb_basename = File.basename(deb_filepath)

# cut up filename to extract package name
# this garish regex finds just the package name and strips the version info, e.g.
# from 'securedrop-ossec-agent-2.8.1+0.3.1-amd64.deb' it will return
# 'securedrop-ossec-agent'
package_name = deb_basename.scan(/^([a-z\-]+(?!\d))/)[0][0].to_s

# ensure required debs appear installable
describe command("dpkg --install --dry-run #{deb_filepath}") do
  its(:exit_status) { should eq 0 }
  its(:stdout) { should contain("Selecting previously unselected package #{package_name}.") }
#    its(:stdout) { should contain("Preparing to unpack #{deb_basename} ...")}
end

# Ensure control fields are populated as expected
describe command("dpkg-deb --field #{deb_filepath}") do
  its(:exit_status) { should eq 0 }
  property['common_deb_package_fields'].each do |field|
    its(:stdout) { should contain(field) }
  end
  its(:stdout) { should contain("Package: #{package_name}")}
  its(:stdout) { should contain("Depends: #{deb_apt_dependencies.join(',')}")}
  its(:stdout) { should contain("Version: #{property['securedrop_app_code_version']}") }
  its(:stdout) { should contain("Description: Packages the SecureDrop application code pip dependencies and AppArmor profiles. This package will put the AppArmor profiles in enforce mode. This package also uses pip to install the pip wheelhouse.") }

  # Regression tests to ensure that undesired fields are not present in the control file.
  its(:stdout) { should_not contain("Conflicts:") }
  its(:stdout) { should_not contain("Replaces:") }
end

describe command(%{dpkg --contents #{deb_filepath} | perl -lane 'print join(" ", @F[0,1,5])' | sort -k 3}) do
  # Regression test to ensure that all files are present in the deb package. Also checks ownership and permissions.
  # If any permissions or files change, this test must be updated. That is intentional.
  # The wacky Perl one-liner parses the tar-format output from dpkg and inspects only permissions,
  # ownership, and filename. Here's an example line from the filtered output:
  #
  #   -rw-r--r-- root/root ./var/www/document.wsgi
  #   drwxr-x--- root/root ./var/www/securedrop/
  #   -rw-r--r-- root/root ./var/www/securedrop/request_that_secures_file_uploads.py
  #   -rw-r--r-- root/root ./var/www/securedrop/template_filters.pyc
  #   -rw-r--r-- root/root ./var/www/securedrop/journalist.pyc
  #
  # The sort pipe ensures that the files are ordered by path name, which is necessary because `dpkg -c` uses
  # tar's formatting by default, which can vary. Sorting before comparison makes diff output useful during failure.

  # TODO: Iron out the permissions issues on these files. The postinst script and the Ansible
  # playbooks are pretty explicit about setting permissions on directories, so it may not be
  # necessary to be draconian with the regression checks. Maybe simple look for filepath equality?
#  its(:stdout) { should eq property['securedrop_app_code_debian_package_contents'] }
  its(:stdout) { should_not match /\/config\.py$/ }
end
