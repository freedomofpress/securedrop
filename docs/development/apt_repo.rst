SecureDrop apt repository
=========================

This document contains a brief description of the Debian packages which are 
hosted and maintained by Freedom of the Press Foundation in our apt repository 
at `apt.freedom.press`_.

linux-image-3.14.*-grsec
    This package contains the Linux kernel image, patched with grsecurity.

linux-headers-3.14.*-grsec
    Header files related to the Linux kernel.

securedrop-app-code
    Packages the SecureDrop application code, Python pip dependencies and 
    AppArmor profiles.

securedrop-ossec-agent
    Installs the pre-configured OSSEC agent for the SecureDrop App Server.

securedrop-ossec-server
    Installs the pre-configured OSSEC manager for the SecureDrop Mon Server.

`securedrop-grsec <https://github.com/freedomofpress/grsec>`_
    SecureDrop grsec kernel (metapackage depending on the latest version).

.. note:: To be added in the future: 

          `securedrop-keyring <https://github.com/freedomofpress/securedrop-keyring>`_    
              Packages the public signing key used in conjunction with this apt           
              repository.               

.. _apt.freedom.press: https://apt.freedom.press
