### To test in prod vms

- `sudo -u www-data bash`
- `cd /var/wwww/securedrop/`
- `./manage.py reset`    # This will clean the DB for testing
- `./create-dev-data.py --staging`

Update this information to the `tests/functional/instance_information.json file.

The content of the file looks like below.

```
{
    "hidserv_token": "asfjsdfag",
    "journalist_location": "http://thejournalistfqb.onion",
    "source_location": "http://thesourceadsfa.onion",
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
cd securedrop
./bin/dev-shell ./bin/run-test -v tests/functional/
```
You may wish to append a pipe to less (i.e. `| less`), as a failure may generate
many pages of output, making it difficult to scroll back.

### Visually see the tests run
Assuming you are on a supported OS that has a vnc client installed. You can run the following to pop open a vnc session to the running tests. This must be done after the tests have started.
