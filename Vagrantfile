# -*- mode: ruby -*-
# vi: set ft=ruby :

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

  config.vm.define 'debs', autostart: false do |debs|
    debs.vm.box = "trusty64"
    debs.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    debs.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-staging.yml"
      ansible.tags = "debs"
    end
    debs.vm.provider "virtualbox" do |v|
      v.name = "debs"
    end
  end

  config.vm.define 'staging', autostart: false do |staging|
    staging.vm.box = "trusty64"
    staging.vm.network "forwarded_port", guest: 80, host: 8082
    staging.vm.network "forwarded_port", guest: 8080, host: 8083
    staging.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    staging.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-staging.yml"
      ansible.tags = "staging"
      ansible.skip_tags = [ 'grsec' ] # options 'tor' 'grsec' 'ssh-hardening' 'iptables' 'tests' 'ossec' also takes an array
    end
    staging.vm.provider "virtualbox" do |v|
      v.name = "staging"
    end
  end

  config.vm.define 'mon', autostart: false do |mon|
    mon.vm.box = "trusty64"
    mon.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    mon.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-mon.yml"
      ansible.tags = "mon"
      ansible.skip_tags = [ 'grsec', 'iptables', 'ssh' ] # options 'tor' 'grsec' 'ssh-hardening' 'iptables' 'tests' 'ossec' also takes an array
    end
    mon.vm.provider "virtualbox" do |v|
      v.name = "mon"
    end
   end

  config.vm.define 'app', autostart: false do |app|
    app.vm.box = "trusty64"
    app.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    app.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-app.yml"
      ansible.tags = "app"
      ansible.skip_tags = [ 'grsec', 'iptables', 'ssh' ] # options 'tor' 'grsec' 'ssh-hardening' 'iptables' 'tests' 'ossec' also takes an array
    end
    app.vm.provider "virtualbox" do |v|
      v.name = "app"
    end
  end

  # "Quick Start" config from https://github.com/fgrehm/vagrant-cachier#quick-start
  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end
end
