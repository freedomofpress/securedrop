# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"
  config.vm.provision :shell,
    inline: "sudo -H -u vagrant /vagrant/setup_dev.sh -r '/home/vagrant/.securedrop' -u"
  config.vm.network "forwarded_port", guest: 8080, host: 8080
  config.vm.network "forwarded_port", guest: 8081, host: 8081
  config.vm.provider "virtualbox" do |v|
    v.name = "securedrop"
  end
end
