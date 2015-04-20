##Running Spec test cheat sheet

serverspec and rspec tests verify the end state of app and monitor servers. The tests are ran remotely from your host system.

###Ubuntu install directions

`apt-get install bundler`
`cd spec_tests/`
`bundle update`
`bundle exec rake spec`

