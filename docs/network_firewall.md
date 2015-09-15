Network Firewall Setup Guide
============================

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Before you begin](#before-you-begin)
    - [3 NIC configuration](#3-nic-configuration)
    - [4 NIC configuration](#4-nic-configuration)
- [Initial Setup](#initial-setup)
  - [Assign interfaces](#assign-interfaces)
  - [Initial configuration](#initial-configuration)
    - [Connect to the pfSense WebGUI](#connect-to-the-pfsense-webgui)
    - [Setup Wizard](#setup-wizard)
    - [Connect Interfaces and Test Connectivity](#connect-interfaces-and-test-connectivity)
- [SecureDrop-specific Configuration](#securedrop-specific-configuration)
  - [Disable DHCP on the LAN](#disable-dhcp-on-the-lan)
    - [Disabling DHCP](#disabling-dhcp)
    - [Assigning a static IP address to the Admin Workstation](#assigning-a-static-ip-address-to-the-admin-workstation)
  - [Set up OPT1](#set-up-opt1)
  - [Set up OPT2](#set-up-opt2)
  - [Set up the network firewall rules](#set-up-the-network-firewall-rules)
    - [Example Screenshots](#example-screenshots)
      - [3 NICs Configuration](#3-nics-configuration)
      - [4 NICs Configuration](#4-nics-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Unfortunately, due to the wide variety of firewalls that may be used, we do not provide specific instructions to cover every type or variation in software or hardware.

This guide will focus on pfSense, and assumes your firewall has at least three interfaces: WAN, LAN, and OPT1.  The latest recommended firewall has four interfaces: WAN, LAN, OPT1, and OPT2. This guide will cover setting up the default NICs for both 3- or 4-NIC configurations on the pfSense firewall.

If your firewall only has 3 NICs (WAN, LAN, and OPT1), you can use the OPT1 interface with a switch on the LAN port. If your firewall has 4 NICs (WAN, LAN, OPT1, and OPT2), a switch will not be required.

To avoid duplication, this guide refers to sections of the [pfSense Guide](http://data.sfb.bg.ac.rs/sftp/bojan.radic/Knjige/Guide_pfsense.pdf), so you will want to have that handy.

Before you begin
----------------

First, consider how the firewall will be connected to the Internet. You need to be able to provision two unique subnets for SecureDrop: the app subnet and the monitor subnet. There are a number of possible ways to configure this, and the best way will depend on the network that you are connecting to.

Note that many firewalls, including the recommended Netgate pfSense, automatically set up the LAN interface on 192.168.1.1/24. The `/24` subnet is a very common choice for home routers. If you are connecting the firewall to a router with the same subnet (common in a small office, home, or testing environment), you will probably be unable to connect to the network at first. However, you will be able to connect from the LAN to the pfSense WebGUI configuration wizard, and from there you will be able to configure the network so it is working correctly.

The app subnet will need at least three IP addresses: one for the gateway, one for the app server, and one for the admin workstation. The monitor subnet will need at least two IP addresses: one for the gateway and one for the monitor server.

We assume that you have examined your network configuration and have selected two appropriate subnets. We will refer to your chosen subnets as "App Subnet" and "Monitor Subnet" throughout the rest of the documentation. 

#### 3 NIC configuration

For the examples in the documentation, we have chosen:

* Admin/App Gateway: 10.20.1.1
* Admin/App Subnet: 10.20.1.0/24

* App Server: 10.20.1.2

* Admin Workstation: 10.20.1.3

* Monitor Subnet: 10.20.2.0/24
* Monitor Gateway: 10.20.2.1
* Monitor Server: 10.20.2.2

#### 4 NIC configuration

For the examples in the documentation, we have chosen:

* Admin Subnet: 10.20.1.0/24
* Admin Gateway: 10.20.1.1
* Admin Workstation: 10.20.1.2

* App Subnet: 10.20.2.0/24
* App Gateway: 10.20.2.1
* App Server: 10.20.2.2

* Monitor Subnet: 10.20.3.0/24
* Monitor Gateway: 10.20.3.1
* Monitor Server: 10.20.3.2

Initial Setup
-------------

Unpack the firewall, connect power, and power on.

### Assign interfaces

Section 3.2.3, "Assigning Interfaces", of the pfSense Guide. Some firewalls, like the Netgate recommended in the Hardware Guide, have this set up already, in which case you can skip this step.

### Initial configuration

We will use the pfSense WebGUI to do the initial configuration of the network firewall.

#### Connect to the pfSense WebGUI

1. Boot the Admin Workstation into Tails from the Admin Live USB.

2. Connect the Admin Workstation to the switch on the LAN.

3. Launch the *Unsafe Browser*, *Applications → Internet → Unsafe Browser*.

   ![Launching the Unsafe Browser](images/firewall/launching_unsafe_browser.png)

    1. Note that the *Unsafe Browser* is, as the name suggests, **unsafe** (its
       traffic is not routed through Tor). However, it is the only option in
       this context because Tails [intentionally][tails_issue_7976] disables
       LAN access in the *Tor Browser*.

    2. A dialog will ask "Do you really want to launch the Unsafe Browser?". Click **Launch**.

       ![You really want to launch the Unsafe Browser](images/firewall/unsafe_browser_confirmation_dialog.png)

    3. You will see a pop-up notification that says "Starting the Unsafe Browser..."

       ![Pop-up notification](images/firewall/starting_the_unsafe_browser.png)

    4. After a few seconds, the Unsafe Browser should launch. The window has a
       bright red border to remind you to be careful when using it. You should
       close it once you're done configuring the firewall and use the Tor
       Browser for any other web browsing you might do on the Admin
       Workstation.

       ![Unsafe Browser Homepage](images/firewall/unsafe_browser.png)

4. Navigate to the pfSense GUI in the *Unsafe Browser*: `https://192.168.1.1`

5. The firewall uses a self-signed certificate, so you will see a "This Connection Is Untrusted" warning when you connect. This is expected (see Section 4.5.6 of the pfSense Guide). You can safely continue by clicking "I Understand the Risks", "Add Exception...", and "Confirm Security Exception."

6. You should see the login page for the pfSense GUI. Log in with the default username and password (admin / pfsense).

[tails_issue_7976]: https://labs.riseup.net/code/issues/7976 "Tails Feature #7976: Disable LAN access in Tor Browser"

#### Setup Wizard

If you're setting up a brand new (or recently factory reset) router, pfSense will start you on the Setup Wizard. Click next, then next again. Don't sign up for a pfSense Gold subscription.

On the "General Information" page, we recommend leaving your hostname as the default (pfSense). There is no relevant domain for SecureDrop, so we recommend setting this to "securedrop.local" or something similar. Use whatever DNS servers you wish. If you don't know what DNS servers to use, we recommend using Google's DNS servers: `8.8.8.8` and `8.8.4.4`. Click Next.

Leave the defaults for "Time Server Information". Click Next.

On "Configure WAN Interface", enter the appropriate configuration for your network. Consult your local sysadmin if you are unsure what to enter here. For many environments, the default of DHCP will work and the rest of the fields can be left blank. Click Next.

For "Configure LAN Interface", set the IP address and subnet mask of the Admin Subnet for the LAN interface.  Be sure that the CIDR prefix correctly corresponds to your subnet mask-- pfsense should automatically calculate this for you, but you should always check. In most cases, your CIDR prefix should be `/24`.  Click Next.

Set a strong admin password. We recommend generating a random password with KeePassX, and saving it in the Tails Persistent folder using the provided KeePassX database template. Click Next.

Click Reload.

If you changed the LAN Interface settings, you will no longer be able to connect after reloading the firewall and the next request will probably time out. This is not a problem - the firewall has reloaded and is working correctly. To connect to the new LAN interface, unplug and reconnect your network cable to have a new network address assigned to you via DHCP. Note that if you used a subnet with fewer addresses than `/24`, the default DHCP configuration in pfSense may not work. In this case, you should assign the Admin Workstation a static IP address that is known to be in the subnet to continue.

Now the WebGUI will be available on the App Gateway address. Navigate to `https://<App Gateway IP>` in the *Unsafe Browser*, and do the same dance as before to log in to the pfSense WebGUI and continue configuring the firewall.

#### Connect Interfaces and Test Connectivity

Now that the initial configuration is completed, you can connect the WAN port without potentially conflicting with the default LAN settings (as explained earlier). Connect the WAN port to the external network. You can watch the WAN entry in the Interfaces table on the pfSense WebGUI homepage to see as it changes from down (red arrow pointing down) to up (green arrow pointing up). The WAN's IP address will be shown once it comes up.

Finally, test connectivity to make sure you are able to connect to the Internet through the WAN. The easiest way to do this is to use ping (Diagnostics → Ping in the WebGUI).

SecureDrop-specific Configuration
---------------------------------

SecureDrop uses the firewall to achieve two primary goals:

1.  Isolating SecureDrop from the existing network, which may be compromised (especially if it is a venerable network in a large organization like a newsroom).
2.  Isolating the app and the monitor servers from each other as much as possible, to reduce attack surface.

In order to use the firewall to isolate the app and monitor servers from each other, we need to connect them to separate interfaces, and then set up firewall rules that allow them to communicate.

### Disable DHCP on the LAN

pfSense runs a DHCP server on the LAN interface by default. At this stage in the documentation, the Admin Workstation has an IP address assigned via that DHCP server. You can easily check your current IP address by *right-clicking* the networking icon (a blue cable going in to a white jack) in the top right of the menu bar, and choosing "Connection Information".

![Connection Information](images/firewall/connection_information.png)

In order to tighten the firewall rules as much as possible, we recommend disabling the DHCP server and assigning a static IP address to the Admin Workstation instead.

#### Disabling DHCP

To disable DHCP, navigate to "Services → DHCP Server". Uncheck the box to "Enable DHCP servers on LAN interface", scroll down, and click the Save button.

#### Assigning a static IP address to the Admin Workstation

Now you will need to assign a static IP to the Admin Workstation. Use the *Admin Workstation IP* that you selected earlier, and make sure you use the same IP when setting up the firewall rules later.

Start by *right-clicking* the networking icon in the top right of the menu bar, and choosing "Edit Connections...".

![Edit Connections](images/firewall/edit_connections.png)

Select "Wired connection" from the list and click the "Edit..." button.

![Edit Wired Connection](images/firewall/edit_wired_connection.png)

Change to the "IPv4 Settings" tab. Change "Method:" from "Automatic (DHCP)" to "Manual". Click the Add button and fill in the static networking information for the Admin Workstation.

![Editing Wired Connection](images/firewall/editing_wired_connection.png)

Click "Save...". If the network does not come up within 15 seconds or so, try disconnecting and reconnecting your network cable to trigger the change. You will need you have succeeded in connecting with your new static IP when you see a pop-up notification that says "Tor is ready. You can now access the Internet".

### Set up OPT1

We set up the LAN interface during the initial configuration. We now need to set up the OPT1 interface. Start by connecting the Application Server to the OPT1 port. Then use the WebGUI to configure the OPT1 interface. Go to `Interfaces → OPT1`, and check the box to "Enable Interface". Use these settings:

-   IPv4 Configuration Type: Static IPv4
-   IPv4 Address: Application Gateway

Once again, be sure that the CIDR prefix correctly corresponds to your subnet mask (and should be `/24` in most cases). Pfsense should automatically calculate this for you, but you should always check.  Leave everything else as the default. Save and Apply Changes.

### Set up OPT2

If you have 4 NICs, you will have to enable the OPT2 interface. Go to `Interfaces → OPT2`, and check the box to "Enable Interface". OPT2 interface is set up similarly to how we set up OPT1 in the previous section. Use these settings:

-   IPv4 Configuration Type: Static IPv4
-   IPv4 Address: Monitor Gateway

Check the CIDR prefix once again (`/24`). Save and Apply Changes.

### Set up the network firewall rules

Since there are a variety of firewalls with different configuration interfaces and underlying sets of software, we cannot provide a set of network firewall rules to match every use case. Instead, we provide a firewall rules template in `install_files/network_firewall/rules`. This template is written in the iptables format, which you will need to manually translate for your firewall and preferred configuration method.

For pfSense, see Section 6 of the pfSense Guide for information on setting up firewall rules through the WebGUI. Here are some tips on interpreting the rules template for pfSense:

1. Create aliases for the repeated values (IPs and ports).
2. pfSense is a stateful firewall, which means that you don't need corresponding rules for the iptables rules that allow incoming traffic in response to outgoing traffic (`--state ESTABLISHED,RELATED`). pfSense does this for you automatically.
3. You should create the rules on the interface where the traffic originates from. The easy way to do this is look at the sources (`-s`) of each of the iptables rules, and create that rule on the corresponding interface.

If you have 3 NICs, your rules are:

  * `-s APP_IP` → `LAN`
  * `-s MONITOR_IP` → `OPT1`

If you have 4 NICs, your rules are:

  * `-s ADMIN_IP` → `LAN`
  * `-s APP_IP` → `OPT1`
  * `-s MONITOR_IP` → `OPT2`

4. Make sure you delete any default "allow all" rules on the LAN interface. Leave the "Anti-Lockout" rule enabled.
5. Any traffic that is not explicitly passed is logged and dropped by default in pfSense, so you don't need to add explicit rules (`LOGNDROP`) for that.
6. Since some of the rules are almost identical except for whether they allow traffic from the App Server or the Monitor Server (`-s MONITOR_IP,APP_IP`), you can use the "add a new rule based on this one" button to save time creating a copy of the rule on the other interface.
7. If you are having trouble with connections, the firewall logs can be very helpful. You can find them in the WebGUI in *Status → System Logs → Firewall*.

We recognize that this process is cumbersome and may be difficult for people inexperienced in managing networks to understand. We are working on automating much of this for the next SecureDrop release.  If you're unsure how to set up your firewall, use the screenshots in the next section as your guide.

#### Example Screenshots

Here are some example screenshots of a working pfSense firewall configuration.

##### 3 NICs Configuration

![Firewall IP Aliases](images/firewall/ip_aliases.png)
![Firewall Port Aliases](images/firewall/port_aliases.png)
![Firewall LAN Rules](images/firewall/lan_rules.png)
![Firewall OPT1 Rules](images/firewall/opt1_rules.png)

##### 4 NICs Configuration

![Firewall IP Aliases](images/firewall/ip_aliases_with_opt2.png)
![Firewall Port Aliases](images/firewall/port_aliases.png)
![Firewall LAN Rules](images/firewall/lan_rules_with_opt2.png)
![Firewall OPT1 Rules](images/firewall/opt1_rules_with_opt2.png)
![Firewall OPT2 Rules](images/firewall/opt2_rules.png)

Once you've set up the firewall, **exit the Unsafe Browser**, and continue with the instructions in the [Install Guide](/docs/install.md#set-up-the-servers).
