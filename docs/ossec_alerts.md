# OSSEC Guide

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Setting up OSSEC alerts](#setting-up-ossec-alerts)
  - [Using Gmail for OSSEC alerts](#using-gmail-for-ossec-alerts)
- [Troubleshooting](#troubleshooting)
- [Analyzing the Alerts](#analyzing-the-alerts)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Setting up OSSEC alerts

OSSEC is an open source host-based intrusion detection system (IDS) that we use to perform log analysis, file integrity checking, policy monitoring, rootkit detection and real-time alerting. It is installed on the Monitor Server and constitutes that machine's main function. OSSEC works in a server-agent scheme, that is, the OSSEC server extends its existing functions to the App Server through an agent installed on that server, covering monitoring for both machines.

In order to receive email alerts from OSSEC, you need to supply several settings to Ansible in the playbook for your environment. If you don't already have a working mail server or don't know what to do, then see the section below about using Gmail as a fallback option. We assume that you're working out of the 'securedrop' directory you cloned the code into, and editing install_files/ansible-base/prod-specific.yml prior to installing SecureDrop.

What you need:
* The GPG key that OSSEC will encrypt alerts to
* The email address that will receive alerts from OSSEC
* Information for your SMTP server or relay (hostname, port) and the fingerprint of its TLS certificate
* Credentials for the email address that OSSEC will send alerts from

Receiving email alerts from OSSEC requires that you have an SMTP relay to route the emails. You can use an SMTP relay hosted internally, if one is available to you, or you can use a third-party SMTP relay such as Gmail. The SMTP relay does not have to be on the same domain as the destination email address, i.e. smtp.gmail.com can be the SMTP relay and the destination address can be securedrop@freedom.press.

While there are risks involved with receiving these alerts, such as information leakage through metadata, we feel the benefit of knowing how the SecureDrop servers are functioning is worth it. If a third-party SMTP relay is used, that relay will be able to learn information such as the IP address the alerts were sent from, the subject of the alerts, and the destination email address the alerts were sent to. Only the body of an alert email is encrypted with the recipient's GPG key. A third-party SMTP relay could also prevent you from receiving any or specific alerts.

The SMTP relay that you use should support SASL authentication and SMTP TLS protocols TLSv1.2, TLSv1.1, and TLSv1. Most enterprise email solutions should be able to meet those requirements.

These are the values you must specify in `prod-specific.yml`:

 * GPG public key used to encrypt OSSEC alerts: `ossec_alert_gpg_public_key`
 * Fingerprint of key used when encrypting OSSEC alerts: `ossec_gpg_fpr`
 * The email address that will receive alerts from OSSEC: `ossec_alert_email`
 * The reachable hostname of your SMTP relay: `smtp_relay`
 * The secure SMTP port of your SMTP relay: `smtp_relay_port`
   (typically 25, 587, or 465. must support TLS encryption)
 * Email username to authenticate to the SMTP relay: `sasl_username`
 * Domain name of the email used to send OSSEC alerts: `sasl_domain`
 * Password of the email used to send OSSEC alerts: `sasl_password`
 * The fingerprint of your SMTP relay: `smtp_relay_fingerprint`

If you don't know what value to enter for one of these, please ask your organization's email administrator for the full configuration before proceeding. It is better to get these right the first time rather than changing them after SecureDrop is installed. If you're not sure of the correct `smtp_relay_port` number, you can use a simple mail client such as Thunderbird to test different settings or a port scanning tool such as nmap to see what's open. You could also use telnet to make sure you can connect to an SMTP server, which will always transmit a reply code of 220 meaning "Service ready" upon a successful connection.

The `smtp_relay` mail server hostname is often, but not always, different from the `sasl_domain`, e.g. smtp.gmail.com and gmail.com.

In some cases, authentication or transport encryption mechanisms will vary and you may require later edits to the Postfix configuration (mainly /etc/postfix/main.cf) on the Monitor Server in order to get alerts to work. You can consult [Postfix's official documentation](http://www.postfix.org/documentation.html) for help, although we've described some common scenarios in the [troubleshooting section](#Troubleshooting) of this document.

If you have your GPG public key handy, copy it to install_files/ansible-base and then specify the filename in the `ossec_alert_gpg_public_key` line of prod-specific.yml.

If you don't have your GPG key ready, you can run GnuPG on the command line in order to find, import and export your public key. It's best to copy the key from a trusted and verified source, but you can also request it from keyservers using the known longid. Looking it up by email address could cause you to obtain a wrong, malicious or expired key. Just replace the key ID in the following example with yours:

Download your key and import it into the local keyring:

	gpg --recv-keys 0xFD720AD9EBA34B1C
	
Export the key to a file:

	gpg --export -a 0xFD720AD9EBA34B1C > ossec.pub
	
Copy the key to a directory where it's accessible by the SecureDrop installation:

	cp ossec.pub install_files/ansible-base/

The fingerprint is a unique identifier for an encryption key that is longer than, but contains both the shortid and longid. The value for `ossec_gpg_fpr` must be the full 40-character GPG fingerprint for this same key, with all capital letters and no spaces.  Here's a series of commands that will retrieve and format the fingerprint per our requirements:

	gpg --with-colons --fingerprint 0xFD720AD9EBA34B1C | grep "^fpr" | cut -d: -f10
	
Next you specify the e-mail that you'll be sending alerts to, as `ossec_alert_email`. This could be your work email, or an alias for a group of IT administrators at your organization. It helps for your mail client to have the ability to filter the numerous messages from OSSEC into a separate folder.
	
Now you can move on to the SMTP and SASL settings, which are straightforward. These correspond to the outgoing e-mail address used to send the alerts instead of where you're receiving them. If that e-mail is ossec@news-org.com, the `sasl_username` would be ossec and `sasl_domain` would be news-org.com.

The Postfix configuration enforces certificate verification, and requires a fingerprint to be set. You can retrieve the fingerprint of your SMTP relay by running the command below (all on one line). Please note that you will need to replace `smtp.gmail.com` and `587` with the correct domain and port for your SMTP relay.

    openssl s_client -connect smtp.gmail.com:587 -starttls smtp < /dev/null 2>/dev/null | openssl x509 -fingerprint -noout -in /dev/stdin | cut -d'=' -f2

If you are using Tails, you will not be able to connect directly with `openssl s_client` due to the default firewall rules. To get around this, proxy the requests over Tor by adding `torify` at the beginning of the command.

The output of the command above should look like the following (*last updated Tue Jul 21 17:46:42 UTC 2015*):

    6D:87:EE:CB:D0:37:2F:88:B8:29:06:FB:35:F4:65:00:7F:FD:84:29

Finally, enter the result as `smtp_relay_fingerprint`. Save `prod-specific.yml`, exit the editor and [proceed with the installation](install.md#install-securedrop) by running the playbooks.

### Using Gmail for OSSEC alerts

It's easy to get SecureDrop to use Google's servers to deliver the alerts, but it's not ideal from a security perspective. This option should be regarded as a backup plan. Keep in mind that you're leaking metadata about the timing of alerts to a third party — the alerts are encrypted and only readable to you, however that timing may prove useful to an attacker.

First you should [sign up for a new account](https://accounts.google.com/SignUp?service=mail). You may use an existing Gmail account, but it's best to compartmentalize these alerts from any of your other activities. Choose a strong and random passphrase. Skip the creation of a Google+ profile and continue straight to Gmail. Once the account is created you can log out and provide the values for `sasl_username` as your new Gmail username (without the domain), `sasl_domain`, which is typically gmail.com (or your custom Google Apps domain), and `sasl_passwd` for the password. The `smtp_relay` is smtp.gmail.com, `smtp_relay_port` is 587 and `smtp_relay_fingerprint` is noted in the example above.

For enhanced security we recommend enabling [Google's 2-Step Verification](https://www.google.com/landing/2step/) for any Gmail account that is dedicated to sending the alert emails. With 2-Step Verification enabled, you won't use the normal account password in this configuration — it will not work; instead you must navigate (using the settings in the top right) to Account > Signing in > App passwords, and generate a new App password which you will use as the `sasl_passwd`.

## Troubleshooting

Some OSSEC alerts should begin to arrive as soon as the installation has finished.

The easiest way to test that OSSEC is working is to SSH to the Monitor Server and run `service ossec restart`. This will trigger an Alert level 3 saying: "Ossec server started."

So you've finished installing SecureDrop, but you haven't received any OSSEC alerts. First, check your spam/junk folder. If they're not in there, then most likely there is a problem with the email configuration. In order to find out what's wrong, you'll have to SSH to the Monitor Server and take a look at the logs. To examine the mail log created by Postfix, run the following command:

	tail /var/log/mail.log
	
The output will show you attempts to send the alerts and provide hints as to what went wrong. Here's a few possibilities and how to fix them:

| Problem  | Solution |
------------- | -------------
| Connection timed out | Check that the hostname and port is correct in the relayhost line of /etc/postfix/main.cf |
| Server certificate not verified | Check that smtp_tls_fingerprint_cert_match in /etc/postfix/main.cf is correct |
| Authentication failure | Edit /etc/postfix/sasl_passwd and make sure the username, domain and password are correct. Run `postmap /etc/postfix/sasl_passwd` to update when finished. |

After making changes to the Postfix configuration, you should run `service postfix reload` and test the new settings by restarting the OSSEC service.

Note that if you change the SMTP relay port after installation for any reason, you must update not only the relayhost in main.cf and contents of sasl_passwd, but also the iptables firewall rules applying to outbound SMTP which are in `/etc/network/iptables/rules_v4`. We recommend modifying and re-running the Ansible playbook instead of doing things like this.

Other log files that may contain useful information:

 * /var/log/procmail.log - there will be lines in this for every alert that gets triggered

 * /var/ossec/logs/ossec.log - OSSEC's general operation is covered here

 * /var/ossec/logs/alerts/alerts.log - contains details of every recent OSSEC alert

 * /var/log/syslog - messages related to grsecurity, AppArmor and iptables

## Analyzing the Alerts

 Understanding the contents of the OSSEC alerts requires a background and knowledge in Linux systems administration. They may be confusing, and at first it will be hard to tell between a genuine problem and a fluke. You should examine these alerts regularly to ensure that the SecureDrop environment has not been compromised in any way, and follow up on any particularly concerning messages with direct investigation.

If you believe that the system is behaving abnormally, you should contact us at support@freedom.press for help.
