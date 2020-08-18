What Makes SecureDrop Unique
============================

SecureDrop attempts to solve or mitigate several problems journalists and sources
have faced in recent legal investigations, attacks from state actors, and other
threats to the confidentiality of communications.

No Third Parties that Can Secretly be Subpoenaed
------------------------------------------------

For decades, there were very few leak prosecutions in the United States in large
part because the government would have to subpoena reporters to testify against
a source to get a conviction. That proved incredibly difficult, if not impossible,
when reporters regularly refused to testify and threatened to go to jail rather
than betray a source.

More recently, there have been a record number of leak prosecutions largely because
the government has learned they don’t need reporters to testify against their
sources anymore. Instead, they can just secretly subpoena third-party services
like Google or AT&T or Verizon or Facebook and get a treasure trove of digital
information on reporters and sources’ communications. For example, the Associated
Press had twenty of their phone lines subpoenaed without their knowledge in order
to identify a source. The government also got a warrant for Fox News reporter James
Rosen’s Gmail account without him knowing. In both cases, their alleged sources
were prosecuted, even though journalists never directly divulged their sources.

SecureDrop completely eliminates third parties from the equation and puts the
power to challenge such cases back in the hands of reporters. The journalist and
source communicate exclusively through one server that the news organization owns
and sits on their property, so any legal order for information must go directly
to the news organization rather than Google or AT&T. The news organization again
has the power to contest the order or refuse to comply if they so wish.

Limits the Metadata Trail as Much as Possible
---------------------------------------------

In many leak cases, the metadata of a journalist's communications—where you’re
located, who you’re talking to, when you’re talking to them, and how often—can
lead to trouble just as much as the actual content of your conversations.

Even if a government serves a court order directly to a news organization to
compel the disclosure of information, SecureDrop logs much less information than
email providers or phone companies do.

The source can only log into SecureDrop through Tor Browser, which masks the
source’s IP address to begin with, so there is no indication who the source is
(unless they disclose it) and where they are sending information from. The Tor IP
address, the computer, and the browser type that the source is using is not logged
either.

For each source, only the time and date of each submission is logged on the
server. When a source sends a new message, the time and date of the last message
is overwritten. This means that there won’t be a trail of metadata showing
exactly when the source and journalist were talking.

In addition, sources cannot create a custom username that could reveal information
about them. Instead, SecureDrop automatically generates two random codenames, one
to show to the source and another to the journalists using the system.

Encrypted and Air-Gapped
------------------------

Communications through SecureDrop are both encrypted in transit, so messages cannot
be easily intercepted and read while they are traversing the Internet and are also
encrypted on the server so if any attacker manages to break into the server, they
would not be able to read past messages.

In addition, the decryption key for SecureDrop submissions sits on an air-gapped
computer (not connected to the Internet). This air-gapped computer is the only
place SecureDrop submissions are decrypted and read so that they are much harder
for an attacker to access.

Protects Against Hackers
------------------------

A 2014 study showed that 21 of the top 25 news organization had, at one time or
another, `been targeted <https://www.reuters.com/article/us-media-cybercrime/journalists-media-under-attack-from-hackers-google-researchers-idUSBREA2R0EU20140328>`__
by state sponsored hackers.

Because of this threat, SecureDrop completely segments its traffic from a news
organization’s normal network. Submissions are accessed and downloaded using the
Tails operating system, which boots off of a USB, does not touch your computer’s
hard drive, and routes all its Internet traffic through Tor.

Submissions are decrypted on an air-gapped computer also using Tails. This
mitigates against the risk that an attacker could send malware through SecureDrop
in an attempt to infect the news organization’s normal network as well.

The SecureDrop servers also undergo significant system hardening in order to make
it as difficult as possible for hackers to break in. By doing so, SecureDrop
protects sources against networks that are already compromised, as well as a news
organization’s normal network from attacks that could potentially come through
SecureDrop.

Free and Open Source Software
-----------------------------

100% of SecureDrop’s code is free and open source. Not only does this mean anyone
can install SecureDrop themselves, but the code is available online for security
experts to test for vulnerabilities.

SecureDrop has gone through four audits by third-party penetration testing firms
and will continue to go through audits when major changes are made to the code
base in the future. We always publish these audits publicly so everyone can be
assured that SecureDrop is as safe to use as possible.
