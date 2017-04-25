# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.define 'build' do |build|
    build.vm.hostname = "build"
    build.vm.box = "bento/ubuntu-14.04"
    build.vm.provision "ansible" do |ansible|
      ansible.playbook = "ansible/build-deb-pkgs.yml"
      ansible.verbose = 'v'
    end
    build.vm.provider "virtualbox" do |v|
      v.name = "ossec-build"
    end
    build.vm.provider "libvirt" do |lv, override|
      lv.memory = 1024
      override.vm.synced_folder './', '/vagrant', type: 'nfs', disabled: false
    end
  end
end
