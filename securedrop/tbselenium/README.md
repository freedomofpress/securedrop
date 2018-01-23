### Install the Python dependencies


```
pip install tbselenium
pip install PyVirtualDisplay==0.2.1
```

### Install Tor Browser 7.0.11

Put it under `~/.local/tbb` directory.
Steps are in `../../install_files/ansible-base/roles/app-test/tasks/install_tbb.yml` file.

### Install geckodriver

This is yet to be in the Ansible.
[Download](https://github.com/mozilla/geckodriver/releases/download/v0.17.0/geckodriver-v0.17.0-linux64.tar.gz) 0.17.0 from
the [release page](https://github.com/mozilla/geckodriver/releases/tag/v0.17.0). Move the binary to `/usr/bin/`.


In this branch, in the securedrop code directory, there is python script `test_utility_cmd.py` which will print you the password, and
TOTP secret.

```
$ python test_utility_cmd.py --username foobar --admin
```

Update this information to the `functional/functional_test.py` in line **100** in `self.journo` value.

### Run the tests

```
$ pytest -v functional/test_admin_interface.py | less
```

Remember to use to pipe to less, or less in case of a failure, there will be too much output.

- `functional/test_source_warnings.py`: THis will fail as we are actually using Tor Browser :)
- `functional/test_submission_not_in_memory.py`: Not inside of the server, so does not make sense.
- `functional/test_source_session_timeout.py`: Remember to change the session time in the server to 0.02 before testing this.
