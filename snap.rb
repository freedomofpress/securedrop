module MyVars
  DIGITAL_OCEAN_API_TOKEN = ''
  # In most documentation the default name used is Vagrant for the ssh keypair
  # for Digital Ocean
  DIGITAL_OCEAN_SSH_KEYFILE_NAME = ''
  # You will need a custom DO image that has a non-root user added with the
  # preconfigured ssh keyfile to use. DO provisions boxes with a defualt user
  # of root which is not allowed with the SecureDrop ssh config.
  DIGITAL_OCEAN_IMAGE_NAME = ''
  # This var should be the repo you want to clone to the development /vagrant
  # dir for the staging environment. A branch should NOT be included. SNAP-CI
  # will handle checking out the correct branch using a built in variable
  # ex: SNAP_CI_REPO_TO_CLONE = 'https://github.com/freedomofpress/securedrop'
  SNAP_CI_REPO_TO_CLONE = ''
end
