Docker Build Maintenance
========================

Get your Quay account squared away
-----------------------------------
The container that performs builds of Debian packages is version controlled in
a docker repository at **quay.io/freedomofpress/sd-docker-builder**.
There are tight restrictions over who can make edits here. If you have permissions
to do so, you'll need to make sure your local docker client has credentials to push.

* First login into your quay.io account via the web-portal at https://quay.io/
* Drill into your **Account settings** via the upper right drop-down (where your username is)
* Click **Generate Encrypted Password**
* From a command-line prompt type **docker login quay.io** with your username and credentials
  obtained from the previous step.
* Proceed with update instructions


Performing container updates
----------------------------
If one of the dependencies requires security updates, the build may fail at
**test_ensure_no_updates_avail** . If you have access rights to push to quay.io,
here is the process to build and push a new container:

.. code:: sh

    cd molecule/builder/
    # Build a new container
    make build-container

Once the container is built, you can push the container to the registry.

.. code:: sh

    make push-container

You can now test the container by going back to the SecureDrop repository root:

.. code:: sh

    cd ../..
    make build-debs

Assuming no errors here, commit the changes in ``molecule/builder/image_hash`` in a branch containing the prefix ``update-builder-``.
