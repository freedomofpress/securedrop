import os
import time

import pytest
import testinfra


@pytest.fixture(autouse=True)
def only_mon_staging_sudo(host):
    if host.backend.host != "mon-staging":
        pytest.skip(f"skipping because this is {host.backend.host} (not mon-staging)")

    with host.sudo():
        yield


def ansible(host, module, parameters):
    r = host.ansible(module, parameters, check=False)
    assert "exception" not in r


def run(host, cmd):
    print(host.backend.host + " running: " + cmd)
    r = host.run(cmd)
    print(r.stdout)
    print(r.stderr)
    return r.rc == 0


def wait_for(fun):
    success = False
    for d in (1, 2, 4, 8, 16, 32, 64):
        if fun():
            success = True
            break
        time.sleep(d)
    return success


def wait_for_command(host, cmd):
    return wait_for(lambda: run(host, cmd))


#
# implementation note: we do not use host.ansible("service", ...
# because it only works for services in /etc/init and not those
# legacy only found in /etc/init.d such as postfix
#
def service_started(host, name):
    assert run(host, f"service {name} start")
    assert wait_for_command(host, f"service {name} status | grep -q 'is running'")


def service_restarted(host, name):
    assert run(host, f"service {name} restart")
    assert wait_for_command(host, f"service {name} status | grep -q 'is running'")


def service_stopped(host, name):
    assert run(host, f"service {name} stop")
    assert wait_for_command(host, f"service {name} status | grep -q 'not running'")


def test_procmail(host):
    service_started(host, "postfix")
    for (destination, f) in (
        ("journalist", "alert-journalist-one.txt"),
        ("journalist", "alert-journalist-two.txt"),
        ("ossec", "alert-ossec.txt"),
    ):
        # Look up CWD, in case tests move in the future
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ansible(host, "copy", "dest=/tmp/{f} src={d}/{f}".format(f=f, d=current_dir))
        assert run(host, "/var/ossec/process_submissions_today.sh forget")
        assert run(host, "postsuper -d ALL")
        assert run(host, f"cat /tmp/{f} | mail -s 'abc' root@localhost")
        assert wait_for_command(host, f"mailq | grep -q {destination}@ossec.test")
    service_stopped(host, "postfix")


def test_process_submissions_today(host):
    assert run(host, "/var/ossec/process_submissions_today.sh " "test_handle_notification")
    assert run(host, "/var/ossec/process_submissions_today.sh " "test_modified_in_the_past_24h")


def test_send_encrypted_alert(host):
    service_started(host, "postfix")
    src = "../../install_files/ansible-base/roles/ossec/files/" "test_admin_key.sec"
    ansible(host, "copy", f"dest=/tmp/test_admin_key.sec src={src}")

    run(host, "gpg  --homedir /var/ossec/.gnupg" " --import /tmp/test_admin_key.sec")

    def trigger(who, payload):
        assert run(host, f"! mailq | grep -q {who}@ossec.test")
        assert run(
            host,
            """
            ( echo 'Subject: TEST' ; echo ; echo -e '{payload}' ) | \
            /var/ossec/send_encrypted_alarm.sh {who}
            """.format(
                who=who, payload=payload
            ),
        )
        assert wait_for_command(host, f"mailq | grep -q {who}@ossec.test")

    #
    # encrypted mail to journalist or ossec contact
    #
    for (who, payload, expected) in (
        ("journalist", "JOURNALISTPAYLOAD", "JOURNALISTPAYLOAD"),
        ("ossec", "OSSECPAYLOAD", "OSSECPAYLOAD"),
    ):
        assert run(host, "postsuper -d ALL")
        trigger(who, payload)
        assert run(
            host,
            """
            job=$(mailq | sed -n -e '2p' | cut -f1 -d ' ')
            postcat -q $job | tee /dev/stderr | \
               gpg --homedir /var/ossec/.gnupg --decrypt 2>&1 | \
               grep -q {expected}
            """.format(
                expected=expected
            ),
        )
    #
    # failure to encrypt must trigger an emergency mail to ossec contact
    #
    try:
        assert run(host, "postsuper -d ALL")
        assert run(host, "mv /usr/bin/gpg /usr/bin/gpg.save")
        trigger(who, "MYGREATPAYLOAD")
        assert run(
            host,
            """
            job=$(mailq | sed -n -e '2p' | cut -f1 -d ' ')
            postcat -q $job | grep -q 'Failed to encrypt OSSEC alert'
            """,
        )
    finally:
        assert run(host, "mv /usr/bin/gpg.save /usr/bin/gpg")
    service_stopped(host, "postfix")


def test_missing_journalist_alert(host):
    #
    # missing journalist mail does nothing
    #
    assert run(
        host,
        """
        JOURNALIST_EMAIL= \
           bash -x /var/ossec/send_encrypted_alarm.sh journalist | \
           tee /dev/stderr | \
           grep -q 'no notification sent'
        """,
    )


# https://ossec-docs.readthedocs.io/en/latest/manual/rules-decoders/testing.html


def test_ossec_rule_journalist(host):
    assert run(
        host,
        """
    set -ex
    l="ossec: output: 'head -1 /var/lib/securedrop/submissions_today.txt"
    echo "$l" | /var/ossec/bin/ossec-logtest
    echo "$l" | /var/ossec/bin/ossec-logtest -U '400600:1:ossec'
    """,
    )


def test_journalist_mail_notification(host):
    mon = host
    app = testinfra.host.Host.get_host(
        "ansible://app-staging", ansible_inventory=host.backend.ansible_inventory
    )
    #
    # run ossec & postfix on mon
    #
    service_started(mon, "postfix")
    service_started(mon, "ossec")

    #
    # ensure the submission_today.txt file exists
    #
    with app.sudo():
        assert run(
            app,
            """
        cd /var/www/securedrop
        ./manage.py were-there-submissions-today
        test -f /var/lib/securedrop/submissions_today.txt
        """,
        )

    #
    # empty the mailq on mon in case there were leftovers
    #
    assert run(mon, "postsuper -d ALL")
    #
    # forget about past notifications in case there were leftovers
    #
    assert run(mon, "/var/ossec/process_submissions_today.sh forget")

    #
    # the command fires every time ossec starts,
    # regardless of the frequency
    # https://github.com/ossec/ossec-hids/issues/1415
    #
    with app.sudo():
        service_restarted(app, "ossec")

    #
    # wait until at exactly one notification is sent
    #
    assert wait_for_command(mon, "mailq | grep -q journalist@ossec.test")
    assert run(mon, "test 1 = $(mailq | grep journalist@ossec.test | wc -l)")

    assert run(mon, "grep --count 'notification suppressed' /var/log/syslog " "> /tmp/before")

    #
    # The second notification within less than 24h is suppressed
    #
    with app.sudo():
        service_restarted(app, "ossec")
    assert wait_for_command(
        mon,
        """
    grep --count 'notification suppressed' /var/log/syslog > /tmp/after
    test $(cat /tmp/before) -lt $(cat /tmp/after)
    """,
    )

    #
    # teardown the ossec and postfix on mon and app
    #
    service_stopped(mon, "postfix")
    service_stopped(mon, "ossec")
    with app.sudo():
        service_stopped(app, "ossec")
