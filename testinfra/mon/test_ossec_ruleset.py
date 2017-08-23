import re


alert_level_regex = re.compile(r"Level: '(\d+)'")


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


def test_overloaded_tor_guard_does_not_produce_alert(Command, Sudo):
    """Check that using an overloaded guard does not produce an OSSEC alert"""
    test_alert = ("Aug 16 21:54:44 app-staging Tor[26695]: [warn] Your Guard "
                  "<name> (<fingerprint>) is failing a very large amount of "
                  "circuits. Most likely this means the Tor network is "
                  "overloaded, but it could also mean an attack against you "
                  "or potentially the guard itself.")

    with Sudo():
        c = Command('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                test_alert))
        assert "Alert to be generated" not in c.stderr


def test_ossec_keep_alive_mark_does_not_produce_alert(Command, Sudo):
    """Check that OSSEC keep alive messages sent to the OSSEC manager
    do not produce OSSEC alerts.

    For more information see:
    https://github.com/ossec/ossec-hids/issues/466
    http://ossec-docs.readthedocs.io/en/latest/faq/alerts.html
    """

    # Example alert from:
    # https://groups.google.com/forum/#!msg/ossec-list/dE3klm84JMU/kGZkRdSl3ZkJ
    test_alert = ("Dec 02 09:48:40 app-staging ossec-keepalive: --MARK--: "
                  "&pQSW__BPa5S?%tyDTJ3-iCG2lz2dU))r(F%6tjp8wqpf=]IKFT%ND2k"
                  "P]ua/W)3-6'eHduX$;$Axqq7Vr.dVZ1SUDSaH)4xTXCIieaEKv47LD-b"
                  "U)SXMnXO/jPGKn3.!NGBR_5]jD2UoSV9)h%z8G%7.xhI;s)267.rV214"
                  "O@t2#w)Z(k'UQp9]MyDERrOrG[-,e?iS@B3Rg/kGiR[g6mc0K)/]S]0'"
                  "+?+'/.[r$fqBR^7iAjoPv4j6SWjeRsLGr%$3#p+buf&u_RC3i/mE3vS3*"
                  "jp&B1qSJM431TmEg,YJ][ge;6-dJI69?-TB?!BI4?Uza63V3vMY3ake6a"
                  "hj-%A-m_5lgab!OVR,!pR+;L]eLgilU")

    with Sudo():
        c = Command('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                    test_alert))
        assert "Alert to be generated" not in c.stderr
