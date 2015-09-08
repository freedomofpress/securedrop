# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.define 'build' do |build|
    build.vm.box = "build"
    build.vm.box = "trusty64"
    build.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    build.vm.provision "ansible" do |ansible|
      ansible.playbook = "ansible/build-deb-pkgs.yml"
      ansible.verbose = 'v'
      ansible.extra_vars = "ansible_vars.json"
    end
    build.vm.provider "virtualbox" do |v|
      v.name = "ossec-build"
    end
  end

end
