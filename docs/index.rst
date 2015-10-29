.. SecureDrop documentation master file, created by
   sphinx-quickstart on Tue Oct 13 12:08:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SecureDrop's documentation!
======================================

SecureDrop is an open-source whistleblower submission system that media
organizations can use to securely accept documents from and communicate with
anonymous sources.

.. toctree::
   :caption: User Guides
   :name: userguidetoc
   :maxdepth: 2

   source
   journalist
   admin

.. toctree::
   :caption: Install SecureDrop
   :name: installtoc
   :maxdepth: 2

   overview
   terminology
   passphrases
   hardware
   before_you_begin
   set_up_tails
   set_up_svs
   set_up_dtd
   generate_securedrop_application_key
   set_up_admin_tails
   network_firewall
   servers
   install
   configure_admin_workstation_post_install
   create_admin_account
   test_the_installation
   onboarding
   
.. toctree::
   :caption: Topic Guides
   :name: topictoc
   :maxdepth: 2

   deployment_practices
   google_authenticator
   logging
   ossec_alerts
   tails_guide
   tails_printing_guide
   training_schedule
   ubuntu_install
   yubikey_setup

.. toctree::
   :caption: Upgrade SecureDrop
   :name: upgradetoc
   :maxdepth: 2

   upgrade/upgrade-0.3.x.rst

.. toctree::
   :caption: Developer Documentation
   :name: devdocs
   :maxdepth: 2
   :glob:

   development/getting_started
   development/*

