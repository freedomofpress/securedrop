class ssh {
  # Declare:
  @@sshkey { $hostname:
    type => 'ecdsa',
    key => $sshecdsakey,
    size => '521',
    #bug in puppet types does not allow setting keytype to correct length
    keytype => 'rsa',
  }
  # Collect:
  Sshkey <<| |>>
}
