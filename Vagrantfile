# -*- mode: ruby -*-
# vi: set ft=ruby :

# Added snap.rb file holds the digital ocean api token values
# so we do not accidently check them into git

require_relative 'snap.rb'
include MyVars

Vagrant.configure("2") do |config|
  config.vm.define 'development', primary: true do |development|
    development.vm.box = "trusty64"
    development.vm.network "forwarded_port", guest: 8080, host: 8080
    development.vm.network "forwarded_port", guest: 8081, host: 8081
    development.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    development.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-development.yml"
      ansible.tags = "development"
      ansible.skip_tags = "tor"
    end
    development.vm.provider "virtualbox" do |v|
      v.name = "development"
    end
  end

  config.vm.define 'app-staging', autostart: false do |app_staging|
    app_staging.vm.box = "trusty64"
    app_staging.vm.network "forwarded_port", guest: 80, host: 8082
    app_staging.vm.network "forwarded_port", guest: 8080, host: 8083
    app_staging.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    app_staging.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-app-staging.yml"
      # options 'tor' 'grsec' 'iptables' 'ssh' 'tests' 'ossec' also takes an array
      ansible.tags = [ 'app-staging', 'debs']
      ansible.skip_tags = [ 'grsec', 'iptables', 'ssh' ]
    end
    app_staging.vm.provider "virtualbox" do |v|
      v.name = "staging"
    end
  end

  config.vm.define 'mon-staging', autostart: false do |mon_staging|
    mon_staging.vm.box = "trusty64"
    mon_staging.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    mon_staging.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-mon-staging.yml"
      # tags: 'tor' 'grsec' 'ssh' 'iptables' 'apparmor-compalin' 'apparmor-enforce' 'tests' also takes an array
      ansible.tags = "mon-staging"
      ansible.skip_tags = [ 'grsec', 'iptables', 'ssh' ]
    end
    mon_staging.vm.provider "virtualbox" do |v|
      v.name = "mon"
    end
   end

  config.vm.define 'app', autostart: false do |app|
    app.vm.box = "trusty64"
    app.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    app.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-app.yml"
      ansible.tags = "app"
      # options 'ssh' 'iptables' 'tests' also takes an array
      ansible.skip_tags = [ 'grsec', 'iptables', 'ssh' ] # options 'tor' 'grsec' 'ssh-hardening' 'iptables' 'tests' 'ossec' also takes an array
    end
    app.vm.provider "virtualbox" do |v|
      v.name = "app"
    end
  end

  config.vm.define 'mon', autostart: false do |mon|
    mon.vm.box = "trusty64"
    mon.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    mon.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-mon.yml"
      # tags: 'tor' 'grsec' 'ssh' 'iptables' 'apparmor-compalin' 'apparmor-enforce' 'tests' also takes an array
      ansible.tags = "mon"
      ansible.skip_tags = [ 'grsec', 'iptables', 'ssh' ]
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
