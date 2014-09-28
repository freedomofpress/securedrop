# -*- mode: ruby -*-
# vi: set ft=ruby :
#require_relative 'secrets'
#include MyVars

Vagrant.configure("2") do |config|
  config.vm.define 'dev' do |dev|
    dev.vm.box = "trusty64"
    dev.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    dev.vm.provision :shell,
      inline: "sudo -H -u vagrant /vagrant/setup_dev.sh -u"
    dev.vm.network "forwarded_port", guest: 8080, host: 8080
    dev.vm.network "forwarded_port", guest: 8081, host: 80
    dev.vm.provider "virtualbox" do |v|
      v.name = "securedrop"
    end
  end
  config.vm.define 'mon' do |mon|
    mon.vm.box = "trusty64"
    mon.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
  end

  config.vm.define 'app' do |app|
    app.vm.box = "trusty64"
    app.vm.network "forwarded_port", guest: 80, host: 8080
    app.vm.network "forwarded_port", guest: 8080, host: 8081
    app.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    app.vm.synced_folder "./", "/vagrant",
      owner: "www-data", group: "www-data"
  end

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "install_files/ansible-base/secureDrop-server.yml"
    ansible.tags = "development"
    ansible.skip_tags = "tor"
  end

  # "Quick Start" config from https://github.com/fgrehm/vagrant-cachier#quick-start
  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end
end
