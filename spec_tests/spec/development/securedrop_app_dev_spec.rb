# development role excludes apache, in favor of flask runner,
# so ensure that apache is not installed.
unwanted_packages = %w(
  securedrop-app-code
  apache2-mpm-worker
  libapache2-mod-wsgi
  libapache2-mod-xsendfile
)
unwanted_packages.each do |unwanted_package|
  describe package(unwanted_package) do
    it { should_not be_installed }
  end
end

# ensure default html dir is absent
describe command("/bin/bash -c '[[ ! -e /var/www/html ]]'") do
  its(:exit_status) { should eq 0 }
end

securedrop_app_directories = [
  TEST_VARS['securedrop_data'],
  "#{TEST_VARS['securedrop_data']}/keys",
  "#{TEST_VARS['securedrop_data']}/tmp",
  "#{TEST_VARS['securedrop_data']}/store",
]
# ensure securedrop app directories exist with correct permissions
securedrop_app_directories.each do |securedrop_app_directory|
  describe file(securedrop_app_directory) do
    it { should be_directory }
    it { should be_owned_by TEST_VARS['securedrop_user'] }
    it { should be_grouped_into TEST_VARS['securedrop_user'] }
    it { should be_mode '700' }
  end
end

# /vagrant has 770 permissions, so test
# separately from the 700 permissions above
describe file(TEST_VARS['securedrop_code']) do
  it { should be_directory }
  it { should be_owned_by TEST_VARS['securedrop_user'] }
  it { should be_grouped_into TEST_VARS['securedrop_user'] }
  it { should be_mode '770' }
end

# ensure cronjob for securedrop tmp dir cleanup is enabled
describe cron do
  # TODO: this should be using TEST_VARS, but the ansible role
  # doesn't use a var, it's hard-coded. update ansible, then fix test.
  # it { should have_entry "@daily #{TEST_VARS['securedrop_code']}/manage.py clean_tmp" }
  it { should have_entry "@daily /var/www/securedrop/manage.py clean_tmp" }
end


# ensure default logo header file exists
# TODO: add check for custom logo header file
describe file("#{TEST_VARS['securedrop_code']}/static/i/logo.png") do
  it { should be_file }
  # TODO: ansible task declares mode 400 but the file ends up as 644 on host
  # TODO: 644 on app-staging, 664 in development
  it { should be_mode '664' }
  it { should be_owned_by TEST_VARS['securedrop_user'] }
  it { should be_grouped_into TEST_VARS['securedrop_user'] }
end
