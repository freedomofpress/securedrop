# declare filenames for built debs
deb_filepath = "/tmp/securedrop-ossec-agent-#{property['ossec_version']}+#{property['securedrop_app_code_version']}-amd64.deb"
deb_apt_dependencies = %w(ossec-agent)

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
  its(:stdout) { should contain("Conflicts: securedrop-ossec-server") }
  its(:stdout) { should contain("Replaces: ossec-agent") }
end

describe command(%{dpkg --contents #{deb_filepath} | perl -lane 'print join(" ", @F[0,1,5])' | sort -k 3}) do
  # Regression test to ensure that all files are present in the deb package. Also checks ownership and permissions.
  # If any permissions or files change, this test must be updated. That is intentional.
  # The wacky Perl one-liner parses the tar-format output from dpkg and inspects only permissions,
  # ownership, and filename. Here's an example line from the filtered output:
  #
  #   drwxr-xr-x root/root ./var/ossec/etc/
  #   -rw-r--r-- root/root ./var/ossec/etc/ossec.conf
  #   -rw-r--r-- root/root ./var/ossec/etc/local_decoder.xml
  #
  # The sort pipe ensures that the files are ordered by path name, which is necessary because `dpkg -c` uses
  # tar's formatting by default, which can vary. Sorting before comparison makes diff output useful during failure.
  its(:stdout) { should eq property['securedrop_ossec_agent_debian_package_contents'] }
end
