# Production hosts will have both FPF repo and Tor Project.
# Staging will have only Tor Project.
describe file("/etc/apt/sources.list.d/#{property['tor_repo_info']['filename']}") do
  its(:content) { should match /^#{Regexp.quote(property['tor_repo_info']['repo_line'])} trusty main$/ }
end

describe command("apt-key export #{property['tor_repo_info']['fingerprint']} | gpg --with-fingerprint --keyring /dev/null") do
  its(:stdout) { should match(/^#{Regexp.quote(property['tor_repo_info']['public_key_info'])}/m) }
end
