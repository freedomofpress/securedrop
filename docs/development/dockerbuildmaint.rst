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

You should get a date tag as a result of the last command above, an example
would be:

.. code:: sh

    Successfully tagged quay.io/freedomofpress/sd-docker-builder:2018_06_06

After you have your new container built, to locally test it, update
**molecule/builder/create.yml** with the following sed one-liner:

.. code:: sh

    # Replace 2018_06_06 with the tag received above
    sed -i 's/@sha256:{{image_hash}}/:2018_06_06/g' create.yml
    cd ../../
    make build-debs


Assuming no errors here, now push the image to **quay.io** and update the molecule
scenario accordingly.

.. code:: sh

    # back we go to the molecule directory
    cd molecule/builder
    # clear out any potential edits you made while testing
    git checkout .
    # push the container you previously built
    make push-container
    # You'll get a digest here copy and replace that in the create playbook
    # for example i received the following mesage
    # 2018_06_06: digest: sha256:15f43e8d86a164509bccbe9b1c9fb5e2b3e6edd87457a9b67fef47574ec8a89c size: 7907
    sed -i "s/docker-builder\:[0-9]*.*/docker-builder\:2018_06_06/g" molecule/builder/create.yml
    sed -i 's/image_hash:.*/image_hash: 15f43e8d86a164509bccbe9b1c9fb5e2b3e6edd87457a9b67fef47574ec8a89c/g' molecule/builder/create.yml


Make sure your changes get committed and merged in. Others will have to re-base on that to take advantage of your changes.
