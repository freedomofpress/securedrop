##Running Spec test cheat sheet

serverspec and rspec tests verify the end state of app and monitor servers. The tests are ran remotely from your host system.

###Ubuntu install directions

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
This will run the tests against all configured hosts. Currently:
* development
* app-staging
* mon-staging
* build

In order to run the tests, each VM will be created and provisioned (if necessary).
Running all VMs concurrently may cause performance problems if you have less
than 8GB of RAM. You can isolate specific machines for fasting testing:

```
cd spec_tests
bundle exec rake --tasks # check output for desired machine
bundle exec rake spec:development
```

