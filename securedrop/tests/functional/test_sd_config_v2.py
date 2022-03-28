from typing import Set
from tests.functional.factories import SecureDropConfigFactory


def _get_public_attributes(obj: object) -> Set[str]:
    attributes = set(
        attr_name for attr_name in dir(obj) if not attr_name.startswith("_")
    )
    return attributes


class TestSecureDropConfigV2:

    def test_v1_and_v2_have_the_same_attributes(self, config, tmp_path):
        sd_config_v1 = config
        sd_config_v2 = SecureDropConfigFactory.create(SECUREDROP_DATA_ROOT=tmp_path)

        attributes_in_sd_config_v1 = _get_public_attributes(sd_config_v1)
        attributes_in_sd_config_v1.remove("env")  # Legacy attribute that's not needed in v2
        attributes_in_sd_config_v2 = _get_public_attributes(sd_config_v2)

        assert attributes_in_sd_config_v1 == attributes_in_sd_config_v2
