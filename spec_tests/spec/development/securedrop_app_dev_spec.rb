require 'spec_helper'

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

