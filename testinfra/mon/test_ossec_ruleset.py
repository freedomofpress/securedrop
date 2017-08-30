import pytest
import re


alert_level_regex = re.compile(r"Level: '(\d+)'")
sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('log_event',
                         sdvars.log_events_without_ossec_alerts)
def test_ossec_false_positives_suppressed(Command, Sudo, log_event):
    with Sudo():
        c = Command('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                log_event["alert"]))
        assert "Alert to be generated" not in c.stderr


def test_grsec_denied_rwx_mapping_produces_alert(Command, Sudo):
    """Check that a denied RWX mmaping produces an OSSEC alert"""
    test_alert = ("Feb 10 23:34:40 app kernel: [  124.188641] grsec: denied "
                  "RWX mmap of <anonymous mapping> by /usr/sbin/apache2"
                  "[apache2:1328] uid/euid:33/33 gid/egid:33/33, parent "
                  "/usr/sbin/apache2[apache2:1309] uid/euid:0/0 gid/egid:0/0")

    with Sudo():
        c = Command('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                test_alert))

        # Level 7 alert should be triggered by rule 100101
        assert "Alert to be generated" in c.stderr
        alert_level = alert_level_regex.findall(c.stderr)[0]
        assert alert_level == "7"


def test_ansible_playbook_triggers_alert(Command, Sudo):
    """When Ansible playbooks are run, an informative alert should be triggered."""

    test_alert = ("Jul 22 17:06:41 app ansible-apt_key: Invoked with file=None "
                  "keyserver=None url=None data=-----BEGIN PGP PUBLIC KEY BLOC"
                  "K-----#012Version: GnuPG "
                  "v1#012#012mQENBEqg7GsBCACsef8koRT8UyZxiv1Irke5nVpte54TDtTl1"
                  "za1tOKfthmHbs2I#0124DHWG3qrwGayw+6yb5mMFe0h9Ap9IbilA5a1IdRs"
                  "dDgViyQQ3kvdfoavFHRxvGON#012tknIyk5Goa36GMBl84gQceRs/4Zx3kx"
                  "qCV+JYXE9CmdkpkVrh2K3j5+ysDWfD/kO#012dTzwu3WHaAwL8d5MJAGQn2"
                  "i6bTw4UHytrYemS1DdG/0EThCCyAnPmmb8iBkZlSW8#0126MzVqTrN37yvY"
                  "WTXk6MwKH50twaX5hzZAlSh9eqRjZLq51DDomO7EumXP90rS5mT#012QrS+"
                  "wiYfGQttoZfbh3wl5ZjejgEjx+qrnOH7ABEBAAG0JmRlYi50b3Jwcm9qZWN"
                  "0#012Lm9yZyBhcmNoaXZlIHNpZ25pbmcga2V5iEYEEBECAAYFAkqqojIACg"
                  "kQ61qJaiiY#012i/WmOgCfTyf3NJ7wHTBckwAeE4MSt5ZtXVsAn0XDq8PWW"
                  "nk4nK6TlevqK/VoWItF#012iEYEEBECAAYFAkqsYDUACgkQO50JPzGwl0vo"
                  "JwCcCSokiJSNY+yIr3nBPN/LJldb#012xekAmwfU60GeaWFwz7hqwVFL23x"
                  "eTpyniEYEEBECAAYFAkt9ndgACgkQYhWWT1sX#012KrI5TACfcBPbsaPA1A"
                  "UVVXXPv0KeWFYgVaIAoMr3jwd1NYVD6Te3D+yJhGzzCD6P#012iEYEEBECA"
                  "AYFAkt+li8ACgkQTlMAGaGhvAU4FwCfX3H4Ggm/x0yIAvmt4CW8AP9F#012"
                  "5D8AoKapuwbjsGncT3UdNFiHminAaq1tiEYEEBECAAYFAky6mjsACgkQhfc"
                  "mMSeh#012yJpL+gCggxs4C5o+Oznk7WmFrPQ3lbnfDKIAni4p20aRuwx6QW"
                  "GH8holjzTSmm5F#012iEYEEBECAAYFAlMI0FEACgkQhEMxewZV94DLagCcD"
                  "G5SR00+00VHzBVE6fDg027e#012N2sAnjNLOYbRSBxBnELUDKC7Vjaz/sAM"
                  "iEwEExECAAwFAkqg7nQFgwll/3cACgkQ#0123nqvbpTAnH+GJA")

    with Sudo():
        c = Command('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                   test_alert))

        assert "Alert to be generated" in c.stderr
