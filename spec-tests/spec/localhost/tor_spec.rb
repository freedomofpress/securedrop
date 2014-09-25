require 'spec_helper'

describe package('tor') do
  it { should be_installed }
end

describe file('/etc/tor/torrc') do
  it { should be_file }
  its(:content) { should match "HiddenServiceAuthorizeClient stealth #{property['hidden_service_authorize_clients_list_key']['document_users']}" }
  its(:content) { should match "HiddenServiceAuthorizeClient stealth #{property['hidden_service_authorize_clients_list_key']['ssh_users']}" }
end

describe command('sudo service tor status') do
  it { should return_exit_status 0 }
end


