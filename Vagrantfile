# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 2.1.2"

Vagrant.configure("2") do |config|

  # Vagrant 1.7.0+ removes the insecure_private_key by default
  # and substitutes a dynamically generated SSH key for each box.
  # Unfortunately this breaks Ansible provisioning with Vagrant,
  # so the key insertion feature should be disabled.
  config.ssh.insert_key = false

  # The prod hosts are just like production but are virtualized.
  # All access to SSH and the web interfaces is only over Tor.
  config.vm.define 'mon-prod', autostart: false do |prod|
    if ENV['SECUREDROP_SSH_OVER_TOR']
      config.ssh.host = find_ssh_aths("mon-ssh-aths")
      config.ssh.proxy_command = tor_ssh_proxy_command
      config.ssh.port = 22
    end
    prod.vm.hostname = "mon-prod"
    prod.vm.box = "bento/ubuntu-20.04"
    prod.vm.network "private_network", ip: "10.0.1.5"
    prod.vm.synced_folder './', '/vagrant', disabled: true
    prod.vm.provider "libvirt" do |lv, override|
      lv.video_type = "virtio"
    end
  end

  config.vm.define 'app-prod', autostart: false do |prod|
    if ENV['SECUREDROP_SSH_OVER_TOR']
      config.ssh.host = find_ssh_aths("app-ssh-aths")
      config.ssh.proxy_command = tor_ssh_proxy_command
      config.ssh.port = 22
    end
    prod.vm.hostname = "app-prod"
    prod.vm.box = "bento/ubuntu-20.04"
    prod.vm.network "private_network", ip: "10.0.1.4"
    prod.vm.synced_folder './', '/vagrant', disabled: true
    prod.vm.provider "libvirt" do |lv, override|
      lv.memory = 1024
      lv.video_type = "virtio"
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

  config.vm.define 'apt-local', autostart: false do |prod|
    prod.vm.hostname = "apt-local"
    prod.vm.box = "bento/ubuntu-20.04"
    prod.vm.network "private_network", ip: "10.0.1.7"
    prod.vm.synced_folder './', '/vagrant', disabled: true
    prod.vm.provider "libvirt" do |lv, override|
      lv.memory = 1024
      lv.video_type = "virtio"
    end
    prod.vm.provision "ansible" do |ansible|
      ansible.playbook = "devops/apt-local.yml"
      ansible.galaxy_role_file = "molecule/upgrade/requirements.yml"
      ansible.galaxy_roles_path = ".galaxy_roles"
      ansible.verbose = 'v'
      # the production playbook verifies that staging default values are not
      # used will need to skip the this role to run in Vagrant
      ansible.raw_arguments = Shellwords.shellsplit(ENV['ANSIBLE_ARGS']) if ENV['ANSIBLE_ARGS']
      # Taken from the parallel execution tips and tricks
      # https://docs.vagrantup.com/v2/provisioning/ansible.html
      ansible.limit = 'all,localhost'
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
