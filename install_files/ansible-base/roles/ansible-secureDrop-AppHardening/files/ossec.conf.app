<ossec_config>
  <client>
    <server-ip>montior</server-ip>
  </client>
  <syscheck>
    <alert_new_files>yes</alert_new_files>

    <directories realtime="yes" check_all="yes" report_changes="yes">/var/ossec</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/etc,/usr/bin,/usr/sbin</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/bin,/sbin</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/var/lib/tor/services/,/var/lib/tor/lock</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/var/www</directories>

    <ignore>/var/www/securedrop/securedrop.log</ignore>
    <ignore>/var/lib/securedrop/keys/pubring.gpg</ignore>
    <ignore>/var/lib/securedrop/keys/secring.gpg</ignore>
    <ignore>/var/lib/securedrop/keys/trustdb.gpg</ignore>
    <ignore>/var/lib/securedrop/store</ignore>
    <ignore>/var/lib/securedrop/db/</ignore>
    <ignore>/var/ossec/queue</ignore>
    <ignore>/var/ossec/logs</ignore>
    <ignore>/var/ossec/stats</ignore>
    <ignore>/var/ossec/var</ignore>
    <ignore>/etc/motd</ignore>
    <ignore>/etc/mtab</ignore>
    <ignore>/etc/mnttab</ignore>
    <ignore>/etc/hosts.deny</ignore>
    <ignore>/etc/mail/statistics</ignore>
    <ignore>/etc/random-seed</ignore>
    <ignore>/etc/adjtime</ignore>
    <ignore>/etc/httpd/logs</ignore>
    <ignore>/etc/utmpx</ignore>
    <ignore>/etc/wtmpx</ignore>
    <ignore>/etc/cups/certs</ignore>
    <ignore>/etc/dumpdates</ignore>
    <ignore>/etc/svc/volatile</ignore>
  </syscheck>
  <rootcheck>
    <rootkit_files>/var/ossec/etc/shared/rootkit_files.txt</rootkit_files>
    <rootkit_trojans>/var/ossec/etc/shared/rootkit_trojans.txt</rootkit_trojans>
    <system_audit>/var/ossec/etc/shared/system_audit_rcl.txt</system_audit>
    <system_audit>/var/ossec/etc/shared/cis_debian_linux_rcl.txt</system_audit>
  </rootcheck>
  <active-response>
    <disabled>yes</disabled>
  </active-response>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/syslog</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/dpkg.log</location>
  </localfile>
  <localfile>
    <log_format>command</log_format>
    <command>df -h</command>
  </localfile>
  <localfile>
    <log_format>full_command</log_format>
    <command>netstat -tan |grep LISTEN |grep -v 127.0.0.1 | sort</command>
  </localfile>
  <localfile>
    <log_format>full_command</log_format>
    <command>last -n 5</command>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/kern.log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/tor/log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/apache2/document-error.log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/apache2/document-access.log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/chroot/source/var/log/tor/log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/www/securedrop/securedrop.log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/unattended-upgrades/unattended-upgrades</location>
  </localfile>
</ossec_config>
