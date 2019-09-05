HTTPS on the *Source Interface*
===============================

The SecureDrop *Source Interface* is served over a Tor Hidden Service,
requiring a ``*.onion`` URL to access it. While Tor Onion Services provide
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

* SecureDrop supports v3 onion services, which use updated cryptographic 
  primitives that provide better transport-layer encryption than those used 
  by v2 onion services. It is **strongly** recommended that you configure your
  instance to use :doc:`v3 onion services <v3_services>`, but if you cannot 
  switch your instance to v3, using HTTPS on the source interface will provide
  an extra layer of encryption for data in transit.

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
available at a `specific URL`_:
``<onion_url>/.well-known/pki-validation/<unique_hash>.txt``.
We have support for this workflow:

.. code:: sh

    # From the Admin Workstation, SSH to the Application Server
    $ ssh app

    # Edit the validation file with content the CA provides
    # Replace <unique_hash> with the token provided by Digicert
    $ sudo vi /var/www/securedrop/.well-known/pki-validation/<unique_hash>.txt

.. note:: If you see "File Not Found" when navigating to this file in Tor Browser,
    check out the latest release in your *Admin Workstation* and re-run
    ``./securedrop-admin install``.

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

.. _`specific URL`: https://www.digicert.com/certcentral-support/use-http-practical-demonstration-dcv-method.htm
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

Make note of the Source Interface Onion URL. Now from ``~/Persistent/securedrop``
on your admin workstation:

.. code:: sh

  ./securedrop-admin sdconfig

This command will prompt you for the following information::

  Whether HTTPS should be enabled on Source Interface (requires EV cert): yes
  Local filepath to HTTPS certificate (optional, only if using HTTPS on source interface): sd.crt
  Local filepath to HTTPS certificate key (optional, only if using HTTPS on source interface): sd.key
  Local filepath to HTTPS certificate chain file (optional, only if using HTTPS on source interface): ca.crt

The filenames should match the names of the files provided to you by DigiCert,
and should be saved inside the ``install_files/ansible-base/`` directory. You'll
rerun the configuration scripts: ::

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
