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
    precise_monitor.ssh.private_key_path = '~/.ssh/if_rsa'
  end

  config.vm.define "wheezy-dev" do |wheezy_dev|
    wheezy_dev.vm.box = "wheezy64"
    wheezy_dev.vm.box_url = "https://dl.dropboxusercontent.com/s/xymcvez85i29lym/vagrant-debian-wheezy64.box"
    wheezy_dev.vm.provision :shell,
      inline: "sudo apt-get update"
  end

  config.vm.provider :digital_ocean do |provider, override|
    override.ssh.private_key_path = '~/.ssh/id_rsa'
    override.vm.box = 'digital_ocean'
    override.vm.box_url = "https://github.com/smdahlen/vagrant-digitalocean/raw/master/box/digital_ocean.box"

    provider.client_id = ''
    provider.api_key = ''
  end

end
