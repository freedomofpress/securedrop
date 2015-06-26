<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Log files cheat sheet](#log-files-cheat-sheet)
  - [Both servers](#both-servers)
  - [App Server](#app-server)
  - [Monitor Server](#monitor-server)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Log files cheat sheet

## Both servers

AppArmor and grsec errors

`/var/log/kern.log`

iptables

`/var/log/syslog`


## App Server

Apache

`/var/log/apache2/*`

If an event triggers it's in the SecureDrop application log

`/var/www/securedrop/securedrop.log`

## Monitor Server

OSSEC

```
/var/ossec/log/ossec.log
/var/ossec/log/alerts/alerts.log
```

Postfix/Procmail

```
/var/log/mail.log
/var/log/procmail.log
```
