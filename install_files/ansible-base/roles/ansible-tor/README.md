Ansible Tor
===========

This is an Ansible role for use with Tor - https://www.torproject.org/

I hope that relay operators will find this useful for deploying
and maintaining large numbers of Tor relays and bridges with
finesse, concurrency and idempotency!

This ansible role can help you reduce the complexity to a single
command for deploying one or more tor relays or tor bridges with or
without obfsproxy.

Here I assume the user has setup their ansible project directory according to the best practices
directory-layout specified here:

http://docs.ansible.com/playbooks_best_practices.html#directory-layout

...and simply run a command like this: ansible-playbook -i production tor-relays.yml

In this case I'm running the tor-relays.yml playbook against
the "production" inventory file. This tor-relays playbook might
specify a host group called tor-relays... which is defined in the
inventory file. I could have many other host groups defined in the
inventory as well such as: tor-exit-relays, tor-bridges,
tor-bananaphone-bridges, tor-hidden-tahoe-storage-nodes etc.



Requirements
------------

Works on Debian and Ubuntu.



Role Variables
--------------

tor_distribution_release should be set to the desired distribution of
the Tor Project's APT repo - http://deb.torproject.org/torproject.org

Perhaps many debian users will want to specify "wheezy"... however if
you intend to operate a tor bridge then you unless you probably want
"tor-experimental-0.2.5.x-wheezy" so that you can have
ServerTransportOptions in your torrc.

tor_obfsproxy_home variable should set when you want to use obfsproxy
with your bridge configuration. Perhaps I should change this to be a
boolean variable names tor_run_obfsproxy... and then set a reasonable
default for the obfsproxy python virtual env directory?

tor_wait_for_hidden_services can be set to yes if you would like the
ansible-tor role to wait for the newly created tor hidden services to
start. It does so by waiting for the tor hidden service hostname file
to appear.



Example Tor Scramblesuit Bridge Playbook
----------------------------------------

This playbook installs and fully configures a scramblesuit
( http://www.cs.kau.se/philwint/scramblesuit/ ) tor bridge using the latest
obfsproxy available to pip (installs into a python virtualenv).

```yml
---

- hosts: tor-bridges
  roles:
    - { role: ansible-role-firewall,
        firewall_allowed_tcp_ports: [ 22, 4703 ],
        sudo: yes
      }
    - { role: david415.ansible-tor,
        tor_distribution_release: "wheezy",
        tor_BridgeRelay: 1,
        tor_PublishServerDescriptor: "bridge",
        tor_obfsproxy_home: "/home/ansible",
        tor_ORPort: 9001,
        tor_ServerTransportPlugin: "scramblesuit exec {{ tor_obfsproxy_home }}/{{ tor_obfsproxy_virtenv }}/bin/obfsproxy --log-min-severity=info --log-file=/var/log/tor/obfsproxy.log managed",
        tor_ServerTransportListenAddr: "scramblesuit 0.0.0.0:4703",
        tor_ExitPolicy: "reject *:*",
        sudo: yes
      }
```


Example Tor Bananaphone Bridge Playbook
---------------------------------------

This playbook demonstrates configuring a tor bridge
with an obfsproxy installed from my git repo so that
the bananaphone pluggable transport is available (it has not been
merged upstream).

Bananaphone provides tor over markov chains!
If you have sensitive or interesting documents then please consider
operating a bananaphone bridge utilizing these text corpuses.
Read about the bananaphone pluggable transport for tor - http://bananaphone.io/


```yml
---

- hosts: tor-bridges
  roles:
    - { role: ansible-role-firewall,
        firewall_allowed_tcp_ports: [ 22, 4703 ],
        sudo: yes
      }
    - { role: david415.ansible-tor,
        tor_distribution_release: "tor-experimental-0.2.5.x-wheezy",
        tor_BridgeRelay: 1,
        tor_PublishServerDescriptor: "bridge",
        tor_obfsproxy_home: "/home/ansible",
        tor_ORPort: 9001,
        tor_obfsproxy_git_url: "git+https://github.com/david415/obfsproxy.git",
        tor_ServerTransportPlugin: "bananaphone exec {{ tor_obfsproxy_home }}/{{ tor_obfsproxy_virtenv }}/bin/obfsproxy --log-min-severity=info --log-file=/var/log/tor/obfsproxy.log managed",
        tor_ServerTransportOptions: "bananaphone corpus=/usr/share/dict/words encodingSpec=words,sha1,4 modelName=markov order=1",
        tor_ServerTransportListenAddr: "bananaphone 0.0.0.0:4703",
        tor_ExitPolicy: "reject *:*",
        sudo: yes
      }
```


Example Tor Relay Playbook
--------------------------


This example playbook sets up tor relays with hidden service for
ssh...

This playbook demonstrates waiting for the hidden services
to be created... by awaiting the existence of the tor hidden service
hostname files. This happens when the role variable
"tor_wait_for_hidden_services" is set to yes.

This feature could be useful when configuring other services that
depend on knowing the hidden service's onion address... such as
my ansible-tahoe-lafs role:
https://github.com/david415/ansible-tahoe-lafs

Read about Tahoe-LAFS here:
https://tahoe-lafs.org/trac/tahoe-lafs
Read about tor hidden services here:
https://www.torproject.org/docs/tor-hidden-service.html.en


```yml
---
- hosts: tor-relays
  user: ansible
  connection: ssh
  vars:
    relay_hidden_services_parent_dir: "/var/lib/tor/services"
    relay_hidden_services: [ { dir: "hidden_ssh",
                               ports: [ { virtport: "22",
                                 target: "localhost:22" } ] }
    ]
  roles:
    - { role: ansible-role-firewall,
        firewall_allowed_tcp_ports: [ 22, 9001 ],
        sudo: yes
      }
    - { role: david415.ansible-tor,
        tor_distribution_release: "wheezy",
        tor_ExitPolicy: "reject *:*",
        tor_hidden_services: "{{ relay_hidden_services }}",
        tor_hidden_services_parent_dir: "{{ relay_hidden_services_parent_dir }}",
        tor_wait_for_hidden_services: yes,
        sudo: yes
      }
```


Example Multi-tor-instance playbook
-----------------------------------


polytorus-ansibilus.yml:
```yml
---
- hosts: tor-relays
  roles:
    - { role: david415.ansible-tor,
        tor_distribution_release: "wheezy",
        tor_ExitPolicy: "reject *:*",
        sudo: yes
      }
```

A simple playbook like this can be used to deploy many instances of
tor on many servers. You can configure multiple tor instances using
the host_vars file for each host.

Here's what an example host_vars file looks like (with rfc1918 ip addrs):

host_vars/192.168.1.1:
```yml
tor_Nickname: [ "ScratchMaster" ]
proc_instances: [ {
name: "relay1",
tor_ORPort: ["192.168.1.1:9002"],
tor_SOCKSPort: ["8041"]
},
{
name: "relay2",
tor_ORPort: ["192.168.1.2:9002"],
tor_SOCKSPort: ["8042"]
},
{
name: "relay3",
tor_ORPort: ["192.168.1.3:9002"],
tor_SOCKSPort: ["8043"]
}]
```

In the above example playbook, all the role variables get applied to
all tor instances. If you want to control the role variables for a
specific host then you must use that host's host_vars file.

Note: when this role is used in "multi-tor process mode"... meaning
that if the proc_instances variable is defined... then the torrc template will set
reasonable defaults for these torrc options: User, PidFile, Log and DataDirectory.

This next example is NOT very practical because it can only be used
with a host inventory with one host! If it were to be used with
multiple hosts then their torrc files would contain the same IP addresses.

```yml
---
- hosts: tor-relays
  roles:
    - { role: david415.ansible-tor,
        tor_distribution_release: "wheezy",
        tor_ExitPolicy: "reject *:*",
        tor_instance_parent_dir: "/etc/tor/instances",
        proc_instances: [ {
                          name: "relay1",
                          tor_ORPort: ["192.168.1.1:9002"],
                          tor_SocksPort: ["8041"]
                        },
                        {
                          name: "relay2",
                          tor_ORPort: ["192.168.1.2:9002"],
                          tor_SocksPort: ["8042"]
                        },
                        {
                          name: "relay3",
                          tor_ORPort: ["192.168.1.3:9002"],
                          tor_SocksPort: ["8043"]
                        }],
        sudo: yes
      }
```


Tor configuration - torrc
-------------------------

torrc may have options set from host_vars/group_vars and
also set from role variables.

The host_vars can set arbitrary torrc configuration options however
the role variables currently support a small subset of the torrc
options at the moment... it's a work in progress; refer to the
templates/torrc for a more detailed overview.

The host_vars variable names must begin with "tor_";
Here's an example setting "Nickname":

```yml
tor_Nickname: [ "OnionRobot" ]
```

The dictionary value is a list because in some cases you may want to
specify multiple lines in the torrc that begin with the dictionary key.


License
-------

MIT


Feature requests and bug-reports welcome!
-----------------------------------------

https://github.com/david415/ansible-tor/issues

