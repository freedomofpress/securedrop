Network Firewall Setup Guide
============================

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
setting up firewall rules through the WebGUI.

Once you've set up the firewall, continue with the installation. Next
step: install Ubuntu on the servers.
