HTTPS on the Source Interface
======================================

The SecureDrop *Source Interface* is served over a Tor Hidden Service,
requiring a ``*.onion`` URL to access it. While Tor Hidden Services provide
end-to-end encryption by default, as well as strong anonymity, there are
several reasons why you might want to consider deploying an additional layer of
encryption and authentication via HTTPS:

* Extended Validation (EV) certificates, which are currently the only type of
  certificates that may be issued for ``*.onion`` addresses, are intended to
  attest to the identity of the organization running a service. This provides
  an additional measure of authenticity (in addition to the organization's
  *Landing Page* and the `SecureDrop Directory`_) to help assure sources that
  they are communicating with the intended organization when they access a
  given Source Interface.

* The cryptographic primitives used by Tor Hidden Services are considered to be
  outdated, and while there are no known compromises of the security of Tor
  Hidden Services due to this issue, you may wish to provide an additional
  layer of transport encryption using stronger cryptographic primitives, which
  is most easily achieved by setting up HTTPS on the Source Interface.

  .. note:: This issue is being addressed by the Tor Project with their Next
     Generation Onion Services design, but the implementation of the new design
     is still a work in progress and is not expected to be deployed until
     December 2017 at the earliest.

.. _`SecureDrop Directory`: https://securedrop.org/directory/

Obtaining an HTTPS certificate for Onion URLs
---------------------------------------------

DigiCert is currently the only Certificate Authority (CA) that issues HTTPS
certificates for ``.onion`` sites. DigiCert requires organizations to follow
the Extended Validation (EV) process in order to obtain a certificate for an
Onion URL, so you should start by reviewing `DigiCert's documentation`_ for
obtaining a ``.onion`` certificate.

The EV certificates display in browsers with a green trust bar, including
information about the organization:

|HTTPS Onion cert|

The additional information about the organization, such as name and geographic
location, are checked by the CA during the EV process. A Source can use this
information to confirm the authenticity of a SecureDrop instance, beyond the
verification already available in the `SecureDrop Directory`_.

In order to obtain an HTTPS certificate for your SecureDrop instance,
`contact DigiCert directly`_. As part of the Extended Validation,
you will be required both to confirm your affiliation with the organization,
and to demonstrate control over the Onion URL for your Source Interface.

In order for you to demonstrate control over the Onion URL for your Source
Interface, DigiCert will provide you with some text and ask you to make it
available at a specific URL: ``<onion_url>/.well-known/pki-validation.html``.
We have support for this workflow:

.. code:: sh

    # From the Admin Workstation, SSH to the Application Server
    $ ssh app

    # Edit the validation file with content the CA provides
    # Note that the filename can be anything as long as it ends
    # with .htm or .html
    $ sudo vi /var/www/securedrop/.well-known/pki-validation.html

While the `CAB forum`_ has specified that ``.onion`` certificates may have a
maximum lifetime of 15 months, we have heard that some folks have run into
issues with such certificates, and currently it seems safest to give the
certificate a validity period of 12 months.

.. tip:: Be patient! HTTPS certificates for ``.onions`` are a recent and fairly
   niche development, so you may run into various issues while trying to obtain
   the certificate.

.. warning:: As part of the process for obtaining an HTTPS certificate, you
   will need to generate a private key. This is usually stored in a file with a
   ``.key`` extension. It is **critical** that you protect this key from
   unauthorized access. We recommend doing this entire process on the Admin
   Workstation, and avoiding copying the ``.key`` to any insecure removable
   media or other computers.

.. _`DigiCert's documentation`: https://www.digicert.com/blog/ordering-a-onion-certificate-from-digicert/
.. |HTTPS Onion cert| image:: images/screenshots/onion-url-certificate.png
.. _`contact DigiCert directly`: https://www.digicert.com/blog/ordering-a-onion-certificate-from-digicert/
.. _`CAB Forum`: https://cabforum.org/2015/02/18/ballot-144-validation-rules-dot-onion-names/

Activating HTTPS in SecureDrop
------------------------------

Make sure you have :doc:`installed SecureDrop already <install>`.

First, on the *Admin Workstation*:

.. code:: sh

  cd ~/Persistent/securedrop

Make note of the Source Interface Onion URL. Edit the site-specific variables
for your organization in
``install_files/ansible-base/group_vars/all/site-specific`` to include the
following: ::

    securedrop_app_https_on_source_interface: yes
    securedrop_app_https_certificate_cert_src: sd.crt
    securedrop_app_https_certificate_key_src: sd.key
    securedrop_app_https_certificate_chain_src: ca.crt

The filenames should match the names of the files provided to you by DigiCert,
and should be saved inside the ``install_files/ansible-base/`` directory. Then rerun
the configuration: ::

    ./securedrop-admin install

The webserver configuration will be updated to apply the HTTPS settings.
Confirm that you can access the Source Interface at
``https://<onion_url>``, and also that the HTTP URL
``http://<onion_url>`` redirects automatically to HTTPS.

.. note:: By default, Tor Browser will send an OCSP request to a Certificate
    Authority (CA) to check if the Source Interface certificate has been revoked.
    Fortunately, this occurs through Tor. However, this means that a CA or anyone
    along the path can learn the time that a Tor user visited the SecureDrop
    Source Interface. Future versions of SecureDrop will add OCSP stapling support
    to remove this request. See `OCSP discussion`_ for the full discussion.

.. _`OCSP discussion`: https://github.com/freedomofpress/securedrop/issues/1941
