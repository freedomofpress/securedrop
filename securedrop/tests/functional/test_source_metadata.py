import requests
from tests.functional import tor_utils
from version import __version__


class TestSourceAppInstanceMetadata:

    def test_instance_metadata(self, sd_servers_v2):
        # Given a source app, when fetching the instance's metadata
        url = f"{sd_servers_v2.source_app_base_url}/metadata"
        response = requests.get(url=url, proxies=tor_utils.proxies_for_url(url))

        # Then it succeeds and the right information is returned
        returned_data = response.json()
        assert returned_data["server_os"] == "20.04"
        assert returned_data["sd_version"] == __version__
        assert returned_data["gpg_fpr"]
