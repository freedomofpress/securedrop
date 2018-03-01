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


### To test in prod vms

- `sudo -u www-data bash`
- `cd /var/wwww/securedrop/`
- `./manage.py reset`    # This will clean the DB for testing
- `./create-demo-user.py`  



Update this information to the `functional/instance_infomration.json file.

The content of the file looks like below.

```
{
    "hidserv_token": "",
    "journalist_location": "http://127.0.0.1:8081",
    "source_location": "http://127.0.0.1:8080",
    "sleep_time": 10,
    "user": {
        "name": "journalist",
        "password": "WEjwn8ZyczDhQSK24YKM8C9a",
        "secret": "JHCOGO7VCER3EJ4L"
    }
}
```

### Run the tests

```
$ pytest -v functional/test_source.py | less
```

Remember to use to pipe to less, or less in case of a failure, there will be too much output.

- `functional/test_source_warnings.py`: THis will fail as we are actually using Tor Browser :)
- `functional/test_submission_not_in_memory.py`: Not inside of the server, so does not make sense.
- `functional/test_source_session_timeout.py`: Remember to change the session time in the server to 0.02 before testing this.
