Securedrop is a tool for communicating securely with journalists.

Securedrop is a server application intended to let news organizations and others set up an online drop box for sources. It's open source software originally created by Aaron Swartz in consultation with a volunteer team of security experts. It is currently maintained by the Freedom of the Press Foundation. In addition to the server application, the project includes installation scripts and set-up instructions both for the software, and for a hardened Ubuntu environment on which to run it.

Securedrop was created with the goal of placing a secure drop box within reach of anyone with the need.

The code is is a Python application that accepts messages and documents from the web and GPG-encrypts them for secure storage. Essentially, it's a more secure alternative to the "contact us" form found on a typical news site.

In operation, every source is given a unique "codename." The codename lets the source establish a relationship with the news organization without revealing her real identity or resorting to e-mail. They can enter the code name on a future visit to read any messages sent back from the journalist -- "Thanks for the Roswell photos! Got any more??" -- or submit additional documents or messages under the same persistent, but anonymous, identifier.

The source is known by a different code name on the journalist's side. All of that source's submissions are grouped together into a "collection." Every time there's a new submission by that source, their collection is bumped to the top of the submission queue.

DeadDrop was designed to use two physical servers: a public-facing server that runs the submisison website and stores messages and documents, and a second that does security monitoring of the first. The New Yorker's public-facing server also has a USB dongle called an Entropy Key plugged attached to generate a pool of random numbers for the crypto.

The original "Deaddrop" web app was coded and architected by [Aaron Swartz](https://github.com/aaronsw). The hardening guide and other security material is the work of [James Dolan](https://github.com/dolanjs). The default web design and the DeadDrop logo were crafted by Dennis Crothers. Journalist [Kevin Poulsen](https://github.com/klpwired) organized the project. The New Yorker launched the first implementation as the New Yorker Strongbox in May 2013. *TODO: describe continued history of the project*