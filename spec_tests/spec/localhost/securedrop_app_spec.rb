#require 'spec_helper'

['/var/www/securedrop'].each do |myDir|
  describe file(myDir) do
    it { should be_directory }
    it { should be_owned_by  'www-data' }
    it { should be_mode '700' }
  end
end

['/var/lib/securedrop','/var/lib/securedrop/store','/var/lib/securedrop/keys'].each do |myDir|
  describe file(myDir) do
    it { should be_directory }
    it { should be_owned_by  'www-data' }
    it { should be_mode '700' }
  end
end

describe file('/var/www/securedrop/config.py') do
  it { should be_file }
  it { should be_owned_by  'www-data' }
  it { should be_mode '600' }
end
