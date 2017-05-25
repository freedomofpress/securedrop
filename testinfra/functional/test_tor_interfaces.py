import os
import re
import pytest

sdvars = pytest.securedrop_test_vars

@pytest.mark.parametrize('site', sdvars.tor_url_files)
@pytest.mark.skipif(os.environ.get('FPF_CI', 'false') == "false",
                    reason="Can only assure Tor is configured in CI atm")
def test_www(Command, site):
    """ 
        Ensure tor interface is reachable and returns expected content
    """

    # extract onion url from saved onion file
    onion_url_raw = open(os.path.dirname(__file__)+"/../../install_files/ansible-base/{}".format(site['file']),'ro').read()
    onion_url = re.search("\w+\.onion", onion_url_raw).group()

    # point curl to our tor proxy box
    curl_tor = "curl -s --socks5-hostname \"${TOR_PROXY}\":9050 "
    site_scrape = Command.check_output(curl_tor+onion_url)
    
    assert Command.check_output(curl_tor+"-o /dev/null -w \"%{http_code}\" "+onion_url) == "200"
    assert site['check_string'] in site_scrape
    assert site['error_string'] not in site_scrape 
