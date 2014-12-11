# SecureDrop Threat Model

This document outlines the threat model for SecureDrop 0.3 and is inspired by the [threat model document Adam Langley wrote for Pond](https://pond.imperialviolet.org/threat.html). The threat model is defined in terms of what each possible adversary can achieve. The list is intended to be exhaustive, i.e. if an entity can do something that is not listed here then that should count as a break of SecureDrop.

##### Assumptions about the journalist or source using SecureDrop:

 * The user acts reasonably and in good faith, e.g. if the user were to give their private key material to the attacker that would be unreasonable.
 * The user obtains an authentic copy of Tails or the Tor Browser.
 
##### Assumptions about the source

 * They would like to not be known as a SecureDrop user, even against a forensic attacker.
 
##### Assumptions about the source's computer

 * The computer correctly executes Tails or the Tor Browser.
 * The computer is not compromised by malware.
 
##### Assumption about the media organization hosting SecureDrop

 * The organization obtains clean hardware for use with SecureDrop.
 * The organization obtains an authentic copy of SecureDrop and its dependencies.
 * The organization follows our [best practice guidelines](https://github.com/freedomofpress/securedrop/blob/develop/docs/deployment_practices.md) when deploying the system.
 * The organization acts in the interest of allowing sources to submit documents, regardless of the contents of these documents.
 * The organization is interested in preserving the anonymity of sources.
 * Those who have physical access to the SecureDrop servers can be trusted to uphold the previous assumptions unless the entire organization has been compromised.
 * The organization may be forced to collude with a government agency to prevent document submissions and attempt to deanonymize sources. This could happen without the knowledge of any third party.
 
##### Assumption about the world

 * The security assumptions of our public cryptosystem (currently RSA 4096-bit keys) are valid.
 * The security assumptions of our hashing/key derivation function (scrypt with randomly-generated salts) are valid.
 * The security/anonymity assumptions of Tor are valid, particularly those of the Tor Hidden Service protocol. This is a somewhat contentious assumption when the application is a web application.
 
##### What a SecureDrop server can and cannot achieve

 * The server sees the plaintext codename, used as the login identifier, of every source.
 * The server sees all HTTP requests made by each source and journalist.
 * The server sees the plaintext documents submitted by each source.
 * The server sees the plaintext communication between a source and a journalist.
 * The server stores a hash, created with scrypt and randomly-generated salts, of a source's codename.
 * The server DOES NOT see the real IP address of a source or journalist, because it is a Hidden Service.
 * The server DOES NOT store plaintext documents or communication on disk.
 * The server DOES NOT store codenames at all on disk.
 
##### What a compromise or physical seizure of the source's property can achieve

 * We assume that some sources will write down or save their codename in order to remember it for future logins. In this case, a compromise or physical seizure of the source's property may result in the attacker obtaining the source's codename.
 * An attacker with the source's codename can login to SecureDrop, submit documents, and communicate with the journalist as that source. The attacker can also see any undeleted messages sent from the journalist to the source.
 
##### What a compromise or physical seizure of the journalist's property can achieve

 * A compromise or physical seizure of the journalist's property may result in the attacker obtaining the login credentials to the SecureDrop *Document Interface*. This means the attacker can see codenames given to sources (not the same as the codenames given to the sources themselves), encrypted submitted documents, and communication with sources. The attacker will be able to continue communicating with the sources.
 * Any decrypted documents stored on the journalist's computer will be available to the attacker. We recommend that journalists encrypt documents with their personal GPG key before taking them off the *Secure Viewing Station*, but we assume they leave documents decrypted while working on them.
 
##### What a compromise or physical seizure of a SecureDrop server can achieve

 * A physical seizure of a SecureDrop server may result in the attacker obtaining the submitted, encrypted documents, the hashes of the source codenames, the replies from journalists that have not yet been read by sources (which are encrypted with a different GPG key per source), and the GPG private key of each source encrypted with the codename of the source as the passphrase.
 * A compromise of a SecureDrop server may allow the attacker to read and modify all plaintext document submissions, undeleted plaintext communication between the journalists and the sources, and plaintext communication between the journalists and sources from the point of compromise onwards. The attacker may also be able to forge messages as any source or journalist.
 * A compromise of a SecureDrop server may allow the attacker to see when journalists, sources, and administrator are accessing the server.
 * A compromise or physical seizure of a SecureDrop server may also result in the attacker gaining access to the scrypt, GPG, and ID pepper values. The attacker may also gain access to logs, including sanitized Tor logs from both Interfaces, error and access logs for the Document Interface and access history and actions performed by the administrator.

##### What a compromise or physical seizure of the Secure Viewing Station can achieve 

 * A physical seizure of the Secure Viewing Station while powered off achieves nothing, assuming that Tails' implementation of full-disk encryption works as expected.
 * A physical seizure of the Secure Viewing Station while powered on, and with the persistent volume mounted, may give the attacker access to the GPG private key used to encrypt and decrypt submitted documents. In addition, the attacker may have access to some plaintext documents that sources have submitted to the organization. Journalists are encouraged to decrypt documents only as needed in separat Tails sessions, wiping the Tails non-persistent volume in between.
 * A compromise of the Secure Viewing Station, while the persistent volume is mounted, may allow the attacker to modify or delete documents before the journalist has had a chance to read them, as well as install or execute binary programs, such as keyloggers.
 * A compromise of the Secure Viewing Station, while the *Transfer Device* is in use, may allow the attacker to copy files to the device used to transfer documents from the Secure Viewing Station to the journalist's workstation. In doing so, the attacker may achieve remote access to any files on the journalist's workstation, including files from SecureDrop, logs, and other plaintext documents.
 
##### What an attacker can achieve when controlling the source's or journalist's network

 * An attacker on, or with control over, the local network can prevent a source or journalist from using SecureDrop by blocking Tor.
  * An attacker on, or with control over, the local network can observe Tor users and may be able to deduce that they are using SecureDrop via traffic analysis (by looking at request sizes, for instance).
 * An attacker capable of viewing the source's network can see the sizes of plaintext uploaded documents.
 * An attacker capable of viewing the journalist's network can see the sizes of encrypted downloaded documents.
 
##### What a global, passive adversary can achieve

* An attacker capable of observing all Internet traffic can possibly detect SecureDrop traffic via traffic analysis and profiling. We have less than 10 HTML pages total on the Source Interface, and most of them are static. Sources using SecureDrop will make a certain sequence of GETs and POSTs, and the response lengths are usually predictable/distinguishable.
* The attacker may be able to link sources or journalists to SecureDrop servers.
* The attacker may be able to link sources to journalists, assuming they are communicating with each other with low-ish latency.
* The attacker may be able to correlate data points during a leak investigation, including looking at who has read up on SecureDrop and who has used Tor.

##### What global, active adversary can achieve

* The attacker may be able to prevent a source or journalist from using SecureDrop by blocking Tor.
* An adversary capable of forging CA certificates may be able to compromise the "landing pages" used by each media organization to communicate instructions for using SecureDrop, as well as the Tor Hidden Service address. This means the attacker can:
	* Trick users into visiting a fraudulent site designed to collect submissions and potentially deanonymize sources by analyzing submission document metadata or convincing them to share identifying information.
	* Trick users into using a compromised version of the Tor Browser, since a download link is usually included on this page.
	
##### What a random person on the Internet can achieve

* A random person can attempt to DoS the SecureDrop server.
* A random person can attempt to trick others into submitting to fake SecureDrop servers.
* A random person can attempt to get sensitive information from a SecureDrop user's browser session, such as CSRF tokens and codenames from cookies.
* A random person can attempt to trick others into downloading a compromised version of Tails or the Tor Browser.
* A random person can attempt to compromise the SecureDrop server by attacking the exposed attack surface, including the kernel network stack, Tor, Apache, the SecureDrop web interfaces, Python, OpenSSH, the TLS implementation, and any other running services.
* A random person can submit forged documents.
* A random person can submit malicious documents, e.g. malware that will attempt to compromise the Secure Viewing Station.