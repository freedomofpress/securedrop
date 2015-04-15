# ensure hosts file references mon server by ip
# TODO: replace hardcoded ip for mon-staging host
describe file('/etc/hosts') do
  its(:content) { should match /^127\.0\.1\.1 app-staging app-staging$/ }
  # TODO: the "securedrop-monitor-server-alias" is an artifact of 
  # using the vagrant-hostmanager plugin. it may no longer be necessary
  its(:content) { should match /^10\.0\.1\.3  mon-staging securedrop-monitor-server-alias$/ }
end
