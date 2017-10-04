# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # Vagrant 1.7.0+ removes the insecure_private_key by default
  # and substitutes a dynamically generated SSH key for each box.
  # Unfortunately this breaks Ansible provisioning with Vagrant,
  # so the key insertion feature should be disabled.
  config.ssh.insert_key = false

  config.vm.define 'development', primary: true do |development|
    development.vm.hostname = "development"
    development.vm.box = "bento/ubuntu-14.04"

    # for hosted docs
    development.vm.network "forwarded_port", guest: 8000, host: 8000, auto_correct: true
    # source interface
    development.vm.network "forwarded_port", guest: 8080, host: 8080, auto_correct: true
    # journalist interface
    development.vm.network "forwarded_port", guest: 8081, host: 8081, auto_correct: true

    development.vm.provision "ansible" do |ansible|
      # Hack to trick Vagrant into parsing the command-line args for
      # Ansible options, see https://gist.github.com/phantomwhale/9657134
      # Example usage:
      #   ANSIBLE_ARGS="--skip-tags=foo" vagrant provision development
      ansible.raw_arguments = Shellwords.shellsplit(ENV['ANSIBLE_ARGS']) if ENV['ANSIBLE_ARGS']
      ansible.playbook = "install_files/ansible-base/securedrop-development.yml"
      ansible.verbose = 'v'
      ansible.groups = {
        'securedrop_application_server' => %w(development),
      }
    end
    # Running the functional tests with Selenium/Firefox has started causing
    # out-of-memory errors.
    #
    # This started around October 14th and was first observed on the task-queue
    # branch. There are two likely causes: (1) The new job queue backend (redis)
    # is taking up a significant amount of memory. According to top, it is not
    # (a couple MB on average). (2) Firefox 33 was released on October 13th:
    # https://www.mozilla.org/en-US/firefox/33.0/releasenotes/ It may require
    # more memory than the previous version did.
    development.vm.provider "virtualbox" do |v|
      v.memory = 1024
      v.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "1"]
    end
    development.vm.provider "libvirt" do |lv, override|
      lv.memory = 1024
      override.vm.synced_folder './', '/vagrant', type: 'nfs', disabled: false
    end
  end

  # The staging hosts are just like production but allow non-tor access
  # for the web interfaces and ssh.
  config.vm.define 'mon-staging', autostart: false do |staging|
    if ENV['SECUREDROP_SSH_OVER_TOR']
      config.ssh.host = find_ssh_aths("mon-ssh-aths")
      config.ssh.proxy_command = tor_ssh_proxy_command
      config.ssh.port = 22
    end
    staging.vm.hostname = "mon-staging"
    staging.vm.box = "bento/ubuntu-14.04"
    staging.vm.network "private_network", ip: "10.0.1.3", virtualbox__intnet: internal_network_name
    staging.vm.synced_folder './', '/vagrant', disabled: true
  end

  config.vm.define 'app-staging', autostart: false do |staging|
    if ENV['SECUREDROP_SSH_OVER_TOR']
      config.ssh.host = find_ssh_aths("app-ssh-aths")
      config.ssh.proxy_command = tor_ssh_proxy_command
      config.ssh.port = 22
    end
    staging.vm.hostname = "app-staging"
    staging.vm.box = "bento/ubuntu-14.04"
    staging.vm.network "private_network", ip: "10.0.1.2", virtualbox__intnet: internal_network_name
    staging.vm.synced_folder './', '/vagrant', disabled: true
    staging.vm.provider "virtualbox" do |v|
      v.memory = 1024
    end
    staging.vm.provider "libvirt" do |lv, override|
      lv.memory = 1024
    end
    staging.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-staging.yml"
      ansible.verbose = 'v'
      # Taken from the parallel execution tips and tricks
      # https://docs.vagrantup.com/v2/provisioning/ansible.html
      ansible.limit = 'all,localhost'
      ansible.raw_arguments = Shellwords.shellsplit(ENV['ANSIBLE_ARGS']) if ENV['ANSIBLE_ARGS']
      ansible.groups = {
        'securedrop_application_server' => %w(app-staging),
        'securedrop_monitor_server' => %w(mon-staging),
        'staging:children' => %w(securedrop_application_server securedrop_monitor_server),
      }
    end
  end

  # The prod hosts are just like production but are virtualized.
  # All access to SSH and the web interfaces is only over Tor.
  config.vm.define 'mon-prod', autostart: false do |prod|
    if ENV['SECUREDROP_SSH_OVER_TOR']
      config.ssh.host = find_ssh_aths("mon-ssh-aths")
      config.ssh.proxy_command = tor_ssh_proxy_command
      config.ssh.port = 22
    end
    prod.vm.hostname = "mon-prod"
    prod.vm.box = "bento/ubuntu-14.04"
    prod.vm.network "private_network", ip: "10.0.1.5", virtualbox__intnet: internal_network_name
    prod.vm.synced_folder './', '/vagrant', disabled: true
  end

  config.vm.define 'app-prod', autostart: false do |prod|
    if ENV['SECUREDROP_SSH_OVER_TOR']
      config.ssh.host = find_ssh_aths("app-ssh-aths")
      config.ssh.proxy_command = tor_ssh_proxy_command
      config.ssh.port = 22
    end
    prod.vm.hostname = "app-prod"
    prod.vm.box = "bento/ubuntu-14.04"
    prod.vm.network "private_network", ip: "10.0.1.4", virtualbox__intnet: internal_network_name
    prod.vm.synced_folder './', '/vagrant', disabled: true
    prod.vm.provider "virtualbox" do |v|
      v.memory = 1024
    end
    prod.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-prod.yml"
      ansible.verbose = 'v'
      # the production playbook verifies that staging default values are not
      # used will need to skip the this role to run in Vagrant
      ansible.raw_arguments = Shellwords.shellsplit(ENV['ANSIBLE_ARGS']) if ENV['ANSIBLE_ARGS']
      # Taken from the parallel execution tips and tricks
      # https://docs.vagrantup.com/v2/provisioning/ansible.html
      ansible.limit = 'all,localhost'
      ansible.groups = {
        'securedrop_application_server' => %w(app-prod),
        'securedrop_monitor_server' => %w(mon-prod),
        'securedrop' => %w(app-prod mon-prod)
      }
    end
  end

end


# Get .onion URL for connecting to instances over Tor.
# The Ansible playbooks fetch these values back to the
# Admin Workstation (localhost) so they can be manually
# added to the inventory file. Possible values for filename
# are "app-ssh-aths" and "mon-ssh-aths".
def find_ssh_aths(filename)
  repo_root = File.expand_path(File.dirname(__FILE__))
  aths_file = File.join(repo_root, "install_files", "ansible-base", filename)
  if FileTest.file?(aths_file)
    File.open(aths_file).each do |line|
      # Take second value for URL; format for the ATHS file is:
      # /^HidServAuth \w{16}.onion \w{22} # client: admin$/
      return line.split()[1]
    end
  else
    puts "Failed to find ATHS file: #{filename}"
    puts "Cannot connect via SSH."
    exit(1)
  end
end

# Build proxy command for connecting to prod instances over Tor.
def tor_ssh_proxy_command
   def command?(command)
     system("which #{command} > /dev/null 2>&1")
   end
  if command?("nc")
    base_cmd = "nc -x"
  else
    puts "Failed to build proxy command for SSH over Tor."
    puts "Install or 'netcat-openbsd'."
    exit(1)
  end
  return "#{base_cmd} 127.0.0.1:9050 %h %p"
end

# Create a unique name for the VirtualBox internal network,
# based on the directory name of the repo. This is to avoid
# accidental IP collisions when running multiple instances
# of the staging or prod environment concurrently.
def internal_network_name
  repo_root = File.expand_path(File.dirname(__FILE__))
  return File.basename(repo_root)
end
