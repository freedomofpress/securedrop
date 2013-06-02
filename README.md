Deaddrop is a tool for communicating securely with journalists.

DeadDrop is a server application intended to let news organizations and others set up an online drop box for sources. It's open source software written by Aaron Swartz in consultation with a volunteer team of security experts. In addition to Aaron's code, the project includes installation scripts and set-up instructions both for the software, and for a hardened Ubuntu environment on which to run it.

DeadDrop was created with the goal of placing a secure drop box within reach of anyone with the need. But at this point expertise is still required to safety deploy this software. And the software itself needs more work.

DeadDrop is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. This program, and all material accompanying it, is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

The code is is a Python application that accepts messages and documents from the web and GPG-encrypts them for secure storage. Essentially, it's a more secure alternative to the "contact us" form found on a typical news site.

In operation, every source is given a unique "codename." The codename lets the source establish a relationship with the news organization without revealing her real identity or resorting to e-mail. She can enter the code name on a future visit to read any messages sent back from the journalist -- "Thanks for the Roswell photos! Got any more??" -- or submit additional documents or messages under the same persistent, but anonymous, identifier.

The source is known by a different code name on the journalist's side. All of that source's submissions are grouped together into a "collection." Every time there's a new submission by that source, their collection is bumped to the top of the submission queue.

DeadDrop was designed to use three physical servers: a public-facing server, a second server for storage of messages and documents, and a third that does security monitoring of the first two. The New Yorker's public-facing server also has a USB dongle called an Entropy Key plugged attached to generate a pool of random numbers for the crypto.

The web app was coded and architected by [Aaron Swartz](https://github.com/aaronsw). The hardening guide and other security material is the work of [James Dolan](https://github.com/dolanjs). The default web design and the DeadDrop logo were crafted by Dennis Crothers. Journalist [Kevin Poulsen](https://github.com/klpwired) organized the project. The New Yorker launched the first implementation as the New Yorker Strongbox in May 2013.

Read `INSTALL.md` for instructions on installing.

Copyright (C) 2011-2012 Aaron Swartz.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.

UK Advanced Cryptics Dictionary Licensing Information:

Copyright © J Ross Beresford 1993-1999. All Rights Reserved. The following restriction is placed on the use of this publication: if the UK Advanced Cryptics Dictionary is used in a software package or redistributed in any form, the copyright notice must be prominently displayed and the text of this document must be included verbatim.
