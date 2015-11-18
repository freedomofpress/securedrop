# Cannot be included in "common" because Staging hosts on DigitalOcean don't have it.
describe file("/etc/apt/sources.list.d/#{property['fpf_repo_info']['filename']}") do
  its(:content) { should match /^#{Regexp.quote(property['fpf_repo_info']['repo_line'])} trusty main$/ }
end

describe command("apt-key export #{property['fpf_repo_info']['fingerprint']} | gpg --with-fingerprint --keyring /dev/null") do
  its(:stdout) { should match(/^#{Regexp.quote(property['fpf_repo_info']['public_key_info'])}/m) }
end
