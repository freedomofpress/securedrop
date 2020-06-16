import pytest
import os
import testinfra
import time


# DRY declaration of why we're skipping all these tests.
# For details, see https://github.com/freedomofpress/securedrop/issues/3689
SKIP_REASON = "unimplemented, see GH#3689"


class TestBase(object):

    @pytest.fixture(autouse=True)
    def only_mon_staging_sudo(self, host):
        if host.backend.host != 'mon-staging':
            pytest.skip()

        with host.sudo():
            yield

    def ansible(self, host, module, parameters):
        r = host.ansible(module, parameters, check=False)
        assert 'exception' not in r

    def run(self, host, cmd):
        print(host.backend.host + " running: " + cmd)
        r = host.run(cmd)
        print(r.stdout)
        print(r.stderr)
        return r.rc == 0

    def wait_for(self, fun):
        success = False
        for d in (1, 2, 4, 8, 16, 32, 64):
            if fun():
                success = True
                break
            time.sleep(d)
        return success

    def wait_for_command(self, host, cmd):
        return self.wait_for(lambda: self.run(host, cmd))

    #
    # implementation note: we do not use host.ansible("service", ...
    # because it only works for services in /etc/init and not those
    # legacy only found in /etc/init.d such as postfix
    #
    def service_started(self, host, name):
        assert self.run(host, "service {name} start".format(name=name))
        assert self.wait_for_command(
            host,
            "service {name} status | grep -q 'is running'".format(name=name))

    def service_restarted(self, host, name):
        assert self.run(host, "service {name} restart".format(name=name))
        assert self.wait_for_command(
            host,
            "service {name} status | grep -q 'is running'".format(name=name))

    def service_stopped(self, host, name):
        assert self.run(host, "service {name} stop".format(name=name))
        assert self.wait_for_command(
            host,
            "service {name} status | grep -q 'not running'".format(name=name))


class TestJournalistMail(TestBase):

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_procmail(self, host):
        self.service_started(host, "postfix")
        for (destination, f) in (
                ('journalist', 'alert-journalist-one.txt'),
                ('journalist', 'alert-journalist-two.txt'),
                ('ossec', 'alert-ossec.txt')):
            # Look up CWD, in case tests move in the future
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.ansible(host, "copy",
                         "dest=/tmp/{f} src={d}/{f}".format(f=f,
                                                            d=current_dir))
            assert self.run(host,
                            "/var/ossec/process_submissions_today.sh forget")
            assert self.run(host, "postsuper -d ALL")
            assert self.run(
                host,
                "cat /tmp/{f} | mail -s 'abc' root@localhost".format(f=f))
            assert self.wait_for_command(
                host,
                "mailq | grep -q {destination}@ossec.test".format(
                    destination=destination))
        self.service_stopped(host, "postfix")

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_process_submissions_today(self, host):
        assert self.run(host,
                        "/var/ossec/process_submissions_today.sh "
                        "test_handle_notification")
        assert self.run(host,
                        "/var/ossec/process_submissions_today.sh "
                        "test_modified_in_the_past_24h")

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_send_encrypted_alert(self, host):
        self.service_started(host, "postfix")
        src = ("../../install_files/ansible-base/roles/ossec/files/"
               "test_admin_key.sec")
        self.ansible(host, "copy",
                     "dest=/tmp/test_admin_key.sec src={src}".format(src=src))

        self.run(host, "gpg  --homedir /var/ossec/.gnupg"
                 " --import /tmp/test_admin_key.sec")

        def trigger(who, payload):
            assert self.run(
                host, "! mailq | grep -q {who}@ossec.test".format(who=who))
            assert self.run(
                host,
                """
                ( echo 'Subject: TEST' ; echo ; echo -e '{payload}' ) | \
                /var/ossec/send_encrypted_alarm.sh {who}
                """.format(who=who, payload=payload))
            assert self.wait_for_command(
                host, "mailq | grep -q {who}@ossec.test".format(who=who))

        #
        # encrypted mail to journalist or ossec contact
        #
        for (who, payload, expected) in (
                ('journalist', 'JOURNALISTPAYLOAD', 'JOURNALISTPAYLOAD'),
                ('ossec', 'OSSECPAYLOAD', 'OSSECPAYLOAD')):
            assert self.run(host, "postsuper -d ALL")
            trigger(who, payload)
            assert self.run(
                host,
                """
                job=$(mailq | sed -n -e '2p' | cut -f1 -d ' ')
                postcat -q $job | tee /dev/stderr | \
                   gpg --homedir /var/ossec/.gnupg --decrypt 2>&1 | \
                   grep -q {expected}
                """.format(expected=expected))
        #
        # failure to encrypt must trigger an emergency mail to ossec contact
        #
        try:
            assert self.run(host, "postsuper -d ALL")
            assert self.run(host, "mv /usr/bin/gpg /usr/bin/gpg.save")
            trigger(who, 'MYGREATPAYLOAD')
            assert self.run(
                host,
                """
                job=$(mailq | sed -n -e '2p' | cut -f1 -d ' ')
                postcat -q $job | grep -q 'Failed to encrypt OSSEC alert'
                """)
        finally:
            assert self.run(host, "mv /usr/bin/gpg.save /usr/bin/gpg")
        self.service_stopped(host, "postfix")

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_missing_journalist_alert(self, host):
        #
        # missing journalist mail does nothing
        #
        assert self.run(
            host,
            """
            JOURNALIST_EMAIL= \
               bash -x /var/ossec/send_encrypted_alarm.sh journalist | \
               tee /dev/stderr | \
               grep -q 'no notification sent'
            """)

    # https://ossec-docs.readthedocs.io/en/latest/manual/rules-decoders/testing.html
    @pytest.mark.skip(reason=SKIP_REASON)
    def test_ossec_rule_journalist(self, host):
        assert self.run(host, """
        set -ex
        l="ossec: output: 'head -1 /var/lib/securedrop/submissions_today.txt"
        echo "$l" | /var/ossec/bin/ossec-logtest
        echo "$l" | /var/ossec/bin/ossec-logtest -U '400600:1:ossec'
        """)

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_journalist_mail_notification(self, host):
        mon = host
        app = testinfra.host.Host.get_host(
            'ansible://app-staging',
            ansible_inventory=host.backend.ansible_inventory)
        #
        # run ossec & postfix on mon
        #
        self.service_started(mon, "postfix")
        self.service_started(mon, "ossec")

        #
        # ensure the submission_today.txt file exists
        #
        with app.sudo():
            assert self.run(app, """
            cd /var/www/securedrop
            ./manage.py were-there-submissions-today
            test -f /var/lib/securedrop/submissions_today.txt
            """)

        #
        # empty the mailq on mon in case there were leftovers
        #
        assert self.run(mon, "postsuper -d ALL")
        #
        # forget about past notifications in case there were leftovers
        #
        assert self.run(mon, "/var/ossec/process_submissions_today.sh forget")

        #
        # the command fires every time ossec starts,
        # regardless of the frequency
        # https://github.com/ossec/ossec-hids/issues/1415
        #
        with app.sudo():
            self.service_restarted(app, "ossec")

        #
        # wait until at exactly one notification is sent
        #
        assert self.wait_for_command(
            mon,
            "mailq | grep -q journalist@ossec.test")
        assert self.run(
            mon,
            "test 1 = $(mailq | grep journalist@ossec.test | wc -l)")

        assert self.run(
            mon,
            "grep --count 'notification suppressed' /var/log/syslog "
            "> /tmp/before")

        #
        # The second notification within less than 24h is suppressed
        #
        with app.sudo():
            self.service_restarted(app, "ossec")
        assert self.wait_for_command(mon, """
        grep --count 'notification suppressed' /var/log/syslog > /tmp/after
        test $(cat /tmp/before) -lt $(cat /tmp/after)
        """)

        #
        # teardown the ossec and postfix on mon and app
        #
        self.service_stopped(mon, "postfix")
        self.service_stopped(mon, "ossec")
        with app.sudo():
            self.service_stopped(app, "ossec")
