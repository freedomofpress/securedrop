# -*- mode: ruby -*-
# vi: set ft=ruby :

# Added snap.rb file holds the digital ocean api token values
# so we do not accidently check them into git

require_relative 'snap.rb'
include MyVars

Vagrant.configure("2") do |config|

  # Requires vagrant plugin vagrant-hostmanger to control the /etc/host entries
  # for non production systems
  # https://github.com/smdahlen/vagrant-hostmanager
  config.hostmanager.enabled = false
  config.hostmanager.manage_host = true
  config.hostmanager.ignore_private_ip = false
  config.hostmanager.include_offline = true

  config.vm.define 'development', primary: true do |development|
    development.vm.hostname = "development"
    development.vm.box = "trusty64"
    development.vm.network "forwarded_port", guest: 8080, host: 8080
    development.vm.network "forwarded_port", guest: 8081, host: 8081
    development.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    development.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/site.yml"
      ansible.verbose = 'v'
    end
    development.vm.provider "virtualbox" do |v|
      v.name = "development"
    end
  end

  config.vm.define 'app-staging', autostart: false do |app_staging|
    app_staging.vm.hostname = "app-staging"
    app_staging.vm.box = "trusty64"
    app_staging.vm.network "private_network", ip: "10.0.1.2", virtualbox__intnet: true
    app_staging.vm.network "forwarded_port", guest: 80, host: 8082
    app_staging.vm.network "forwarded_port", guest: 8080, host: 8083
    app_staging.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    app_staging.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/site.yml"
      # options 'tor' 'grsec' 'iptables' 'ssh' 'tests' 'ossec' also takes an array
      ansible.skip_tags = [ 'grsec' ]
      ansible.verbose = 'v'
    end
    app_staging.vm.provider "virtualbox" do |v|
      v.name = "app-staging"
    end
  end

  config.vm.define 'mon-staging', autostart: false do |mon_staging|
    mon_staging.vm.hostname = "mon-staging"
    mon_staging.vm.box = "trusty64"
    mon_staging.vm.network "private_network", ip: "10.0.1.3", virtualbox__intnet: true
    mon_staging.hostmanager.aliases = %w(securedrop-monitor-server-alias)
    mon_staging.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    mon_staging.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/site.yml"
      # tags: 'tor' 'grsec' 'ssh' 'iptables' 'apparmor-complain' 'apparmor-enforce' 'tests' also takes an array
      ansible.skip_tags = [ 'grsec' ]
      ansible.verbose = 'v'
    end
    mon_staging.vm.provider "virtualbox" do |v|
      v.name = "mon-staging"
    end
   end

  config.vm.define 'app', autostart: false do |app|
    app.vm.hostname = "app"
    app.vm.box = "trusty64"
    app.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    app.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/site.yml"
      # options 'ssh' 'iptables' 'tests' also takes an array
      ansible.skip_tags = [ 'grsec' ] # options 'tor' 'grsec' 'ssh-hardening' 'iptables' 'tests' 'ossec' also takes an array
      ansible.verbose = 'v'
    end
    app.vm.provider "virtualbox" do |v|
      v.name = "app"
    end
  end

  config.vm.define 'mon', autostart: false do |mon|
    mon.vm.box = "mon"
    mon.vm.box = "trusty64"
    mon.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    mon.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/site.yml"
      # tags: 'tor' 'grsec' 'ssh' 'iptables' 'apparmor-compalin' 'apparmor-enforce' 'tests' also takes an array
      ansible.skip_tags = [ 'grsec' ]
      ansible.verbose = 'v'
    end
    mon.vm.provider "virtualbox" do |v|
      v.name = "mon"
    end
  end

  # "Quick Start" config from https://github.com/fgrehm/vagrant-cachier#quick-start
  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  # This is needed for the Snap-ci to provision the digital ocean vps
  config.vm.provider :digital_ocean do |provider, override|
    override.ssh.private_key_path = "/var/snap-ci/repo/id_rsa"
    override.vm.box = 'digital_ocean'
    override.vm.box_url = "https://github.com/smdahlen/vagrant-digitalocean/raw/master/box/digital_ocean.box"
    provider.token = SNAP_API_TOKEN
    provider.image = 'snapVagrantSSHkey'
    provider.region = 'nyc2'
    provider.size = '512mb'
  end
end
