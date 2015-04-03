module MyVars
  DIGITAL_OCEAN_API_TOKEN = ''
  # In most documentation the default name used is Vagrant for the ssh keypair
  # for Digital Ocean
  DIGITAL_OCEAN_SSH_KEYFILE_NAME = ''
  # You will need a custom DO image that has a non-root user added with the
  # preconfigured ssh keyfile to use. DO provisions boxes with a defualt user
  # of root which is not allowed with the SecureDrop ssh config.
  DIGITAL_OCEAN_IMAGE_NAME = ''
end
