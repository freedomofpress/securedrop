Testing SecureDrop
==================

The SecureDrop project ships both application code for running on servers
hosted on-site at news organizations, as well as configuration scripts
for provisioning the servers to accept updates to the application code,
and to harden the system state. Therefore testing for the project includes
:ref:`Application Tests<app_tests>` for validating that the app code behaves
as expected, and :ref:`Configuration Tests<config_tests>` to ensure that the
servers are appropriately locked down, and able to accept updates to the app code.

In addition, the :ref:`Continuous Integration<ci_tests>` automatically runs
the above Application and Configuration tests against cloud hosts,
to aid in PR review.
