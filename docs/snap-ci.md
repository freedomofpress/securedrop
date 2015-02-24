# running notes on setting up snap-ci + vagrant + digital ocean provider + ansible provisioner

To speed up testing times, prebuilt images that already contain the packages needed for each stage are used.
The prebuilt images are snapshots of the default VPS Ubuntu 14.04 x64 images with the stage specific deb packages installed.
After the stage specific packages are installed a snapshot is taken of the image with the stage name and date.

To test a clean install there is a manual gate to run the snap-ci tests without the prebuilt images

(This should be migrated to Packer)

# Development

git clone https://github.com/freedomofpress/securedrop
sudo apt-get install gnupg2 haveged python python-pip secure-delete sqlite libssl-dev python-dev python-pip firefox xvfb redis-server
sudo pip install -r securedrop/requirements/securedrop-requirements.txt
sudo pip install -r securedrop/requirements/test-requirements.txt

# App-staging

git clone https://github.com/freedomofpress/securedrop
sudo apt-get install apache2-mpm-worker libapache2-mod-xsendfile libapache2-mod-wsgi apparmor-utils gnupg2 haveged python python-pip secure-delete sqlite libssl-dev python-dev python-pip firefox xvfb tar unzip inotify-tools libssl-dev redis-server
sudo pip install -r securedrop/requirements/securedrop-requirements.txt

# mon-staging


# In Snap-CI
