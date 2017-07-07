HTTPS on the Source Interface
======================================

The *Source Interface* for SecureDrop is automatically served over
as a Tor Hidden Service, requiring a ``*.onion`` URL to access it.
While Tor Hidden Services provide end-to-end encryption by default, as well
as strong anonymity, there are several reasons why you might want to consider
deploying an additional layer of encryption and authentication via HTTPS:

* The cryptographic primitives used by Tor Hidden Services are considered to be
  outdated, and while there are no known compromises of the security of Tor
  Hidden Services due to this issue, it may be wise to provide an additional
  layer of transport encryption using stronger cryptographic primitives, which
  is most easily achieved by setting up HTTPS on the Source Interface.

  .. note:: This issue is being addressed by the Tor Project with their Next
     Generation Onion Services design, but that design is still a work in
     progress and is not expected to be deployed until December 2017 at the
     soonest.

* Extended Validation (EV) certificates, which are currently the only type of
  certificates that may be issued for ``*.onion`` addresses, are intended to
  attest to the identity of the organization running a service. This provides
  an additional measure of authenticity (in addition to the organization's
  *Landing Page* and the `SecureDrop Directory`_) to help assure sources that
  they are communicating with the intended organization when they access a
  given Source Interface.

.. _`SecureDrop Directory`: https://securedrop.org/directory/

Obtaining an HTTPS certificate for Onion URLs
---------------------------------------------

DigiCert is currently the only registrar that issues Onion-compatible HTTPS
certificates, and requires organizations to follow the Extended Validation (EV)
process in order to `obtain a certificate for an Onion URL`_. The EV certificates
display in browsers with a green trust bar, including information about
the organization:

|HTTPS Onion cert|

.. _`obtain a certificate for an Onion URL`: https://www.digicert.com/blog/ordering-a-onion-certificate-from-digicert/
.. |HTTPS Onion cert| image:: images/screenshots/onion-url-certificate.png

The additional information about the organization, such as name and geographic
location, are checked by the registrar during the EV process. A Source can
use this information to confirm the authenticity of a SecureDrop instance,
beyond the verification already available in the `SecureDrop Directory`_.

.. _`SecureDrop Directory`: https://securedrop.org/directory/

In order to obtain an HTTPS certificate for your SecureDrop instance,
`contact DigiCert directly`_. As part of the Extended Validation,
you will be required both to confirm your affiliation with the organization,
and to demonstrate control over the Onion URL for your Source Interface.

.. _`contact DigiCert directly`: https://www.digicert.com/blog/ordering-a-onion-certificate-from-digicert/

Activating HTTPS in SecureDrop
------------------------------

Make sure you have :doc:`installed SecureDrop already <install>`, and made
note of the Source Interface Onion URL. Edit the site-specific variables
for your organization in ``install_files/ansible-base/group_vars/all/site-specific``
to include the following: ::

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
``https://<your_domain>.onion``, and also that the HTTP URL
``http://<your_domain.onion`` redirects automatically to HTTPS.
