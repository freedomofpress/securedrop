import json

from sdconfig import JournalistInterfaceConfig, SourceInterfaceConfig


def make_config(tmpdir, is_journalist):
    name = 'journalist' if is_journalist else 'source'
    filename = '{}-config.json'.format(name)
    with open(str(tmpdir.join(filename)), 'w') as f:
        f.write(json.dumps({
            'journalist_key': 'foo',
            'scrypt_gpg_pepper': 'bar',
            'scrypt_id_pepper': 'baz',
            'secret_key': 'quux',
        }))


def check_config(config):
    assert config.DEFAULT_LOCALE == 'en_US'
    assert config.SUPPORTED_LOCALES == ['en_US']
    assert config.SCRYPT_PARAMS == dict(N=2**14, r=8, p=1)
    assert config.CUSTOM_HEADER_IMAGE is None


def test_journalist_config_defaults(tmpdir):
    make_config(tmpdir, True)
    config = JournalistInterfaceConfig(str(tmpdir))
    check_config(config)


def test_source_config_defaults(tmpdir):
    make_config(tmpdir, False)
    config = SourceInterfaceConfig(str(tmpdir))
    check_config(config)
