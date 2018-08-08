import io
import os
import re
import pytest

TOR_URL_FILES = [{'file': 'app-source-ths',
                  'check_string': 'SUBMIT DOCUMENTS',
                  'error_string': "ERROR"}]

testinfra_hosts = ["docker://apptestclient"]


@pytest.mark.parametrize('site', TOR_URL_FILES)
def test_www(host, site):
    """
    Ensure tor interface is reachable and returns expected content.
    """

    # Extract Onion URL from saved onion file, fetched back from app-staging.
    onion_url_filepath = os.path.join(
        os.path.dirname(__file__),
        "../../../install_files/ansible-base/{}".format(site['file'])
    )
    onion_url_raw = io.open(onion_url_filepath, 'r').read()
    onion_url = re.search("\w+\.onion", onion_url_raw).group()

    # Fetch Onion URL via curl to confirm interface is rendered correctly.
    curl_tor = 'curl -s --socks5-hostname "${{TOR_PROXY}}":9050 {}'.format(
        onion_url)
    curl_tor_status = '{} -o /dev/null -w "%{{http_code}}"'.format(curl_tor)

    site_scrape = host.check_output(curl_tor)
    assert host.check_output(curl_tor_status) == "200"
    assert site['check_string'] in site_scrape
    assert site['error_string'] not in site_scrape
