SecureDrop Overview
===================

SecureDrop is an open-source whistleblower submission system that media organizations can use to securely accept documents from and communicate with anonymous sources. It was originally created by the late Aaron Swartz and is currently managed by [Freedom of the Press Foundation][FPF].

Infrastructure
--------------

![SecureDrop architecture overview diagram](./SecureDrop_diagram.png)

There are four main components of SecureDrop: the servers, the administrators, the sources, and the journalists.

At SecureDrop's heart is a pair of severs: the *Application (“App”) Server* which runs the core SecureDrop software, and the *Monitor (“Mon”) Server* which keeps track of the *Application Server* and sends out alerts if there's a problem. These two servers run on dedicated hardware connected to a dedicated firewall appliance. They are typically located physically inside the newsroom.

The SecureDrop servers are managed by a systems administrator; for larger newooms, there may be a team of systems administrators. The administrator uses a dedicated *Admin Workstation* running [Tails]() and connects to the App and Mon servers over authenticated [Tor Hidden Services]() and manages them using [Ansible]().

A source submits documents and messages by using [Tor Browser]() (or Tails) to access the *Source Interface*: a public Tor Hidden Service. Submissions are encrypted in place on the App server as they are uploaded.

Journalists working in the newsroom use two machines to interact with SecureDrop. First, they use a *Journalist Workstation* running Tails to connect to the *Document Interface*, an authenticated Tor Hidden Service. Journalists download [GPG]()-encrypted submissions and copy them to a *Transfer Device* (a thumb drive or DVD). Those submissions are then connected to the airgapped *Secure Viewing Station* (SVS) which holds the key to decrypt them. Journalists can then use the SVS to read, print, and otherwise prepare documents for publication. Apart from those deliberately published, decrypted document are never accessed on an Internet-connected computer.

The terms in italics are terms of art specific to SecureDrop. The [Terminology Guide](./terminology.md) provides more-precise definitions of these and other terms. SecureDrop is designed against a comprehensive [threat model](./thread-model.md), and has a specific notion of the [roles](./roles.md) that are involved in its operation.

[FPF]: https://freedom.press
[Tails]: https://tails.boum.org
[Tor Hidden Services]: https://www.torproject.org/docs/hidden-services.html
[Ansible]: http://www.ansible.com/
[Tor Browser]: https://www.torproject.org/projects/torbrowser.html
[GPG]: https://www.gnupg.org/

