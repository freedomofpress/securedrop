# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # Vagrant 1.7.0+ removes the insecure_private_key by default
  # and substitutes a dynamically generated SSH key for each box.
  # Unfortunately this breaks Ansible provisioning with Vagrant,
  # so the key insertion feature should be disabled.
  config.ssh.insert_key = false

  config.vm.define 'development', primary: true do |development|
    development.vm.hostname = "development"
    development.vm.box = "trusty64"
    development.vm.network "forwarded_port", guest: 8080, host: 8080
    development.vm.network "forwarded_port", guest: 8081, host: 8081
    development.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    development.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-development.yml"
      ansible.skip_tags = ENV['DEVELOPMENT_SKIP_TAGS'] || 'non-development'
      ansible.verbose = 'v'
    end
    development.vm.provider "virtualbox" do |v|
      v.name = "development"
      # Running the functional tests with Selenium/Firefox has started causing out-of-memory errors.
      #
      # This started around October 14th and was first observed on the task-queue branch. There are two likely causes:
      # 1. The new job queue backend (redis) is taking up a significant amount of memory. According to top, it is not (a couple MB on average).
      # 2. Firefox 33 was released on October 13th: https://www.mozilla.org/en-US/firefox/33.0/releasenotes/ It may require more memory than the previous version did.
      v.memory = 1024
    end
  end

  # The staging hosts are just like production but allow non-tor access
  # for the web interfaces and ssh.
  config.vm.define 'mon-staging', autostart: false do |staging|
    staging.vm.hostname = "mon-staging"
    staging.vm.box = "trusty64"
    staging.vm.network "private_network", ip: "10.0.1.3", virtualbox__intnet: true
    staging.hostmanager.aliases = %w(securedrop-monitor-server-alias)
    staging.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    staging.vm.synced_folder './', '/vagrant', disabled: true
    staging.vm.provider "virtualbox" do |v|
      v.name = "mon-staging"
    end
  end

  config.vm.define 'app-staging', autostart: false do |staging|
    staging.vm.hostname = "app-staging"
    staging.vm.box = "trusty64"
    staging.vm.network "private_network", ip: "10.0.1.2", virtualbox__intnet: true
    staging.vm.network "forwarded_port", guest: 80, host: 8082
    staging.vm.network "forwarded_port", guest: 8080, host: 8083
    staging.vm.synced_folder './', '/vagrant', disabled: true
    staging.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    staging.vm.provider "virtualbox" do |v|
      v.name = "app-staging"
      # Running the functional tests with Selenium/Firefox has started causing out-of-memory errors.
      #
      # This started around October 14th and was first observed on the task-queue branch. There are two likely causes:
      # 1. The new job queue backend (redis) is taking up a significant amount of memory. According to top, it is not (a couple MB on average).
      # 2. Firefox 33 was released on October 13th: https://www.mozilla.org/en-US/firefox/33.0/releasenotes/ It may require more memory than the previous version did.
      v.memory = 1024
    end
    staging.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-staging.yml"
      ansible.verbose = 'v'
      # Taken from the parallel execution tips and tricks
      # https://docs.vagrantup.com/v2/provisioning/ansible.html
      ansible.limit = 'all'
      ansible.tags = ENV['STAGING_TAGS']
      # Quickest boot
      #ansible.skip_tags = [ "common", "ossec", 'app-test' ]
      # Testing the web application installing local securedrop-app-code deb
      # package
      #ansible.skip_tags = [ "common", "ossec", 'fpf_repo' ]
      # Testing the web app from repo
      #ansible.skip_tags = [ "install_local_pkgs", "common", "ossec" ]
      # Creating the apparmor profiles
      #ansible.skip_tags = [ "grsec",  "ossec", "app-test" ]
      # Testing the full install install with local access exemptions
      # This requires to also up mon-staging or else authd will error
      ansible.skip_tags = ENV['STAGING_SKIP_TAGS'] || 'install_local_pkgs'
    end
  end

  # The prod hosts are just like production but are virtualized. All access to ssh and
  # the web interfaces is only over tor.
  config.vm.define 'mon-prod', autostart: false do |prod|
    prod.vm.box = "mon-prod"
    prod.vm.box = "trusty64"
    prod.vm.network "private_network", ip: "10.0.1.5", virtualbox__intnet: true
    prod.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    prod.vm.synced_folder './', '/vagrant', disabled: true
    prod.vm.provider "virtualbox" do |v|
      v.name = "mon-prod"
    end
  end

  config.vm.define 'app-prod', autostart: false do |prod|
    prod.vm.hostname = "app-prod"
    prod.vm.box = "trusty64"
    prod.vm.network "private_network", ip: "10.0.1.4", virtualbox__intnet: true
    prod.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    prod.vm.synced_folder './', '/vagrant', disabled: true
    prod.vm.provider "virtualbox" do |v|
      v.name = "app-prod"
      # Running the functional tests with Selenium/Firefox has started causing out-of-memory errors.
      #
      # This started around October 14th and was first observed on the task-queue branch. There are two likely causes:
      # 1. The new job queue backend (redis) is taking up a significant amount of memory. According to top, it is not (a couple MB on average).
      # 2. Firefox 33 was released on October 13th: https://www.mozilla.org/en-US/firefox/33.0/releasenotes/ It may require more memory than the previous version did.
      v.memory = 1024
    end
    prod.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/securedrop-prod.yml"
      ansible.verbose = 'v'
      # the production playbook verifies that staging default values are not
      # used will need to skip the this role to run in Vagrant
      ansible.skip_tags = ENV['PROD_SKIP_TAGS']
      # Taken from the parallel execution tips and tricks
      # https://docs.vagrantup.com/v2/provisioning/ansible.html
      ansible.limit = 'all'
    end
  end

  config.vm.define 'build', autostart: false do |build|
    build.vm.box = "build"
    build.vm.box = "trusty64"
    build.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
    build.vm.provision "ansible" do |ansible|
      ansible.playbook = "install_files/ansible-base/build-deb-pkgs.yml"
      ansible.verbose = 'v'
      ansible.skip_tags = ENV['BUILD_SKIP_TAGS']
    end
    build.vm.provider "virtualbox" do |v|
      v.name = "build"
    end
  end

  # "Quick Start" config from https://github.com/fgrehm/vagrant-cachier#quick-start
  #if Vagrant.has_plugin?("vagrant-cachier")
  #  config.cache.scope = :box
  #end

  # This is needed for the Snap-ci to provision the digital ocean vps.
  # Check for presence of digitalocean vagrant plugin, and required env var,
  # and only configure this provider if both conditions are met. Otherwise,
  # even running `vagrant status` throws an error.
  if Vagrant.has_plugin?('vagrant-digitalocean') and ENV['DO_API_TOKEN']
    config.vm.provider :digital_ocean do |provider, override|
      # In snap-ci the contents of the ssh keyfile should be saved as a `Secure
      # Files` to the default locations /var/snap-ci/repo/id_rsa and
      # /var/snap-ci/repo/id_rsa.pub
      override.ssh.private_key_path = ENV['DO_SSH_KEYFILE'] || '/var/snap-ci/repo/id_rsa'
      override.vm.box = 'digital_ocean'
      override.vm.box_url = 'https://github.com/smdahlen/vagrant-digitalocean/raw/master/box/digital_ocean.box'

      # Ansible playbooks will handle SecureDrop configuration,
      # but DigitalOcean boxes don't have a default "vagrant" user configured.
      # The below settings will allow the vagrant-digitalocean plugin to configure
      # sudoers acccess for the user "vagrant"
      provider.setup = true
      override.ssh.username = 'vagrant'

      # Ansible playbooks sudoers config will clobber the vagrant-digitalocean plugin config,
      # so drop in a sudoers.d file to ensure that the vagrant user still has password-less sudo.
      # This mimicks the admin typing in a sudo password during the first Ansible task in production.
      override.vm.provision :shell,
        inline: "echo 'vagrant ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/vagrant && chmod 0440 /etc/sudoers.d/vagrant"
      # The shell provisioner will generate an error: "stdin: is not a tty" in Ubuntu,
      # due to vagrant forcing "bash -l" as a login shell. See here for more info:
      # https://github.com/mitchellh/vagrant/issues/1673

      provider.token = ENV['DO_API_TOKEN']
      provider.region = ENV['DO_REGION'] || 'sfo1'
      provider.size = ENV['DO_SIZE'] || '512mb'

      # The vagrant-digitalocean plugin changed how it handles
      # the 'provider.image' parameter starting in v0.7.1,
      # breaking support for snapshots. Snapshots are useful
      # when running app tests since box creation happens much faster.
      # This format works for <= 0.7.0:
      #provider.image = ENV['DO_IMAGE_NAME'] || '14.04 x64'
      # This format works for >= 0.7.1:
      provider.image = ENV['DO_IMAGE_NAME'] || 'ubuntu-14-04-x64'
    end
  end
end
