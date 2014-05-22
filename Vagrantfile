# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.define "precise-dev" do |precise_dev|
    precise_dev.vm.box = "precise64"
    precise_dev.vm.box_url = "https://dl.dropboxusercontent.com/s/xymcvez85i29lym/vagrant-ubuntu-precise64.box"
    precise_dev.vm.provision :shell,
      inline: "sudo -u vagrant /vagrant/securedrop/setup_dev.sh -r '/home/vagrant/.securedrop' -u"
      precise_dev.vm.network "forwarded_port", guest: 8080, host: 8080
      precise_dev.vm.network "forwarded_port", guest: 8081, host: 8081
  end

  config.vm.define "precise-app" do |precise_app|
    precise_app.vm.box = "precise64"
    precise_app.vm.box_url = "https://dl.dropboxusercontent.com/s/xymcvez85i29lym/vagrant-ubuntu-precise64.box"
  end

  config.vm.define "precise-monitor" do |precise_monitor|
    precise_monitor.vm.box = "precise64"
    precise_monitor.vm.box_url = "https://dl.dropboxusercontent.com/s/xymcvez85i29lym/vagrant-ubuntu-precise64.box"
  end
end
