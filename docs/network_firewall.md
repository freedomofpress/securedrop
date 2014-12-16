Network Firewall Setup Guide
============================

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Initial Setup](#initial-setup)
- [Assign interfaces](#assign-interfaces)
- [Configure Firewall](#configure-firewall)
  - [General configuration](#general-configuration)
  - [SecureDrop-specific configuration](#securedrop-specific-configuration)
    - [Choose IPs](#choose-ips)
    - [Set up OPT1](#set-up-opt1)
    - [Set up firewall rules](#set-up-firewall-rules)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Unfortunately, due to the wide variety of firewalls that may be used, we
do not provide specific instructions to cover every type or variation in
software or hardware.

This guide will focus on pfSense, and assumes your firewall has at
least three interfaces: WAN, LAN, and OPT1. These are the default
interfaces on the recommended Netgate firewall, and it should be easy
to configure any pfSense firewall with 3 or more NICs this way.

To avoid duplication, this guide refers to sections of the
[pfSense Guide](http://data.sfb.bg.ac.rs/sftp/bojan.radic/Knjige/Guide_pfsense.pdf),
so you will want to have that handy.

Initial Setup
-------------

Unpack the firewall, connect power, and power on.

Assign interfaces
-----------------

Section 3.2.3, "Assigning Interfaces", of the pfSense Guide.

Some firewalls, like the Netgate recommended in the Hardware Guide,
have this set up already, in which case you can skip this step.

Configure Firewall
------------------

### General configuration

1.  Connect cable from modem to the firewall's WAN port. You may need
    to power cycle the modem to get your ISP to assign an IP address
    to the WAN interface's MAC address via DHCP, particularly if that
    modem was previously attached to a different router.
2.  Connect the switch to the LAN port.
3.  Connect the Admin Workstation to the switch to administer firewall.
4.  Do the initial configuration of pfSense through the WebGUI. Follow
    the instructions in the pfSense Guide, starting with section 4.1,
    "Connecting to the WebGUI".
5.  Test connectivity to make sure you are able to connect to the
    Internet through the WAN. The easiest way to do this is probably
    ping (Diagnostics > Ping in the WebGUI).

### SecureDrop-specific configuration

SecureDrop uses the firewall to achieve two primary goals:

1.  Isolating SecureDrop from the existing network, which may be
    compromised (especially if it is a venerable network in a large
    organization like a newsroom).
2.  Isolating the app and the monitor servers from each other as much as
    possible, to reduce attack surface.

In order to use the firewall to isolate the app and monitor servers from
each other, we need to connect them to separate interfaces, and then set
up firewall rules that allow them to communicate.

#### Choose IPs

First, choose static IP addresses for the app and monitor servers. The
rest of this guide will assume the following choice of IP addresses:

* App Server: `192.168.1.2`
* Monitor Server: `192.168.2.2`

This choice of IPs implies:

1.  The App server will be connected to the LAN, since its IP is in
    the default LAN subnet of `192.168.1.1/24`.
2.  The Monitor server will be connected to OPT1, and we will need to
    configure OPT1 accordingly.

#### Set up OPT1

Go to `Interfaces > OPT1`, and check the box to "Enable Interface". Use
these settings:

-   IPv4 Configuration Type: Static IP
-   IPv4 Address: 192.168.2.1/24

Leave everything else as the default. Save and Apply Changes.

#### Set up firewall rules

Since there are a variety of firewalls with different configuration
interfaces and underlying sets of software, we cannot provide a set of
network firewall rules to match every use case. Instead, we provide a
firewall rules template in `install_files/network_firewall/rules`.
This template is written in the iptables format, which you will need
to manually translate for your firewall and preferred configuration
method.

For pfSense, see Section 6 of the pfSense Guide for information on
setting up firewall rules through the WebGUI. Here are some tips on
interpreting the rules template for pfSense:

1. We recommend creating aliases for the repeated values (IPs and
   FQDNs). This will make your rules easier to read later.
2. pfSense is a stateful firewall, which means that you don't need the
   iptables rules that allow incoming traffic that's in response to
   outgoing traffic (`--state ESTABLISHED,RELATED`). pfSense does this
   for you automatically.
3. You should create the rules on the interface where the traffic
   originates from. The easy way to do this is look at the sources
   (`-s`) of each iptables rules, and create that rule on each
   corresponding interface. In case this is not clear:

	* `-s APP_IP` => LAN
	* `-s MONITOR_IP` => OPT1
4. Make sure you delete the default "allow all" rule on the LAN
   interface.

We recognize that this process is cumbersome and may be difficult for
people inexperienced in managing networks to understand. We are
working on automating much of this for the next SecureDrop release.

Once you've set up the firewall, continue with the installation. Next
step: install Ubuntu on the servers.
