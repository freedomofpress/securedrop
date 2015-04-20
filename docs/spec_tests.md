# Serverspec tests

[serverspec](http://serverspec.org/) tests verify the end state of the vagrant machines. 
Any changes to the Ansible configuration should have a corresponding spectest.

##Install directions (Ubuntu)
```
apt-get install bundler
cd spec_tests/
bundle update
```

###Running the tests

```
cd spec_tests/
bundle exec rake spec
```
This will run the tests against all configured hosts, specifically: 
* development
* app-staging
* mon-staging
* build

In order to run the tests, each VM will be created and provisioned, if necessary.
Running all VMs concurrently may cause performance problems if you have less
than 8GB of RAM. You can isolate specific machines for faster testing:

```
cd spec_tests
bundle exec rake --tasks # check output for desired machine
bundle exec rake spec:development
```

