import os
import re
import pytest

sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('site', sdvars.tor_url_files)
@pytest.mark.skipif(os.environ.get('FPF_CI', 'false') == "false",
                    reason="Can only assure Tor is configured in CI atm")
def test_www(host, site):
    """
    Ensure tor interface is reachable and returns expected content.
    """

    # Extract Onion URL from saved onion file, fetched back from app-staging.
    onion_url_filepath = os.path.join(
        os.path.dirname(__file__),
        "../../install_files/ansible-base/{}".format(site['file'])
    )
    onion_url_raw = open(onion_url_filepath, 'ro').read()
    onion_url = re.search("\w+\.onion", onion_url_raw).group()

    # Fetch Onion URL via curl to confirm interface is rendered correctly.
    curl_tor = 'curl -s --socks5-hostname "${{TOR_PROXY}}":9050 {}'.format(
        onion_url)
    curl_tor_status = '{} -o /dev/null -w "%{{http_code}}"'.format(curl_tor)

    site_scrape = host.check_output(curl_tor)
    assert host.check_output(curl_tor_status) == "200"
    assert site['check_string'] in site_scrape
    assert site['error_string'] not in site_scrape
