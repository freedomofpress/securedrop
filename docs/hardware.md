# Hardware for SecureDrop

This document outlines requirements and recommended hardware for use with SecureDrop. If you have any questions, please contact securedrop@pressfreedomfoundation.org. 

## SecureDrop infrastructure

The SecureDrop infrastructure consists of different components, all of which are listed below. We recommend you read the through the whole document and figure out what makes the most sense for your organization.

### App Server and Monitor Server

The *Application Server* (or *App Server* for short) runs the SecureDrop application. This server hosts both the website that sources access (*Source Interface*) and the website that journalists access (*Document Interface*). The *Monitor Server* keeps track of the *App Server* and sends out an email alert if something seems wrong. SecureDrop requires that you have:

 * 1 x physical server for the *Application Server*, which will run the SecureDrop application.
 * 1 x physical server for the *Monitor Server*, which sends emails about issues with the *App Server*.
 
The SecureDrop application requires a 64-bit operating system. For this reason, we recommend you get two [Intel NUCs](http://www.amazon.com/dp/B00F3F38O2/ref=wl_it_dp_o_pd_nS_ttl?_encoding=UTF8&colid=3NQVTBFZV73JA&coliid=IOKQL5QS1Q2NX&psc=1) with powercords. Additionally, you will need to get the following [two 240 GB hard drives](http://www.amazon.com/dp/B00BQ8RKT4/ref=wl_it_dp_o_pd_nS_ttl?_encoding=UTF8&colid=3NQVTBFZV73JA&coliid=I319YS8KKXVZWS&psc=1) and a [16 GB (8GBx2) memory kit](http://www.amazon.com/Crucial-PC3-12800-204-Pin-Notebook-CT2CP25664BF160B/dp/B005MWQ6WC/ref=sr_1_2?s=electronics&ie=UTF8&qid=1411294165&sr=1-2).
 
### Secure Viewing Station

The *Secure Viewing Station* is a machine that is kept offline and only ever used together with the Tails operating system. This machine will be used to generate GPG keys for all journalists with access to SecureDrop, as well as decrypt and view submitted documents. Since this machine will never touch the Internet or run an operating system other than Tails, it does not need a hard drive or network device. We recommend the following:

 * 1 x laptop without a hard drive, network interface card or wireless units.
 * 1 x encrypted, external hard drive to store documents on while working on a story.
 * 1 x offline printer.
 
We recommend that you either buy or repurpose an old laptop. Another option is to buy an [Intel NUC](http://www.amazon.com/dp/B00F3F38O2/ref=wl_it_dp_o_pd_nS_ttl?_encoding=UTF8&colid=3NQVTBFZV73JA&coliid=IOKQL5QS1Q2NX&psc=1) with a powercord and [8 GB of memory](http://www.amazon.com/Crucial-PC3-12800-204-Pin-Notebook-CT2CP25664BF160B/dp/B005MWQ6WC/ref=sr_1_2?s=electronics&ie=UTF8&qid=1411294165&sr=1-2), but note that you will also need to get a monitor and a wired keyboard and mouse. For the external drive and the printer, we recommend the [WD My Passport external drive](http://www.amazon.com/Passport-Ultra-Portable-External-Backup/dp/B00E83X9P8/ref=sr_1_1?s=electronics&ie=UTF8&qid=1411330862&sr=1-1) and [HP Deskjet printer](http://www.amazon.com/HP-Deskjet-Printer-CH340A-B1H/dp/B003YGZIY0/ref=pd_sim_op_2?ie=UTF8&refRID=1BNF29AQ5S6C3SR0DS6V).
 
### Tails and Transfer Devices

The *Transfer Device* is the physical media used to transfer encrypted documents from the *Journalist Workstation* to the *Secure Viewing Station*. Additional devices are needed to run Tails. We recommend the following:

 * 1 x physical media for the system administrator to run Tails on.
 * 1 x physical media for the system administrator to transfer files on.
 * 1 x physical media for the journalist to run Tails on.
 * 1 x physical media for the journalist to transfer files on.
 * 1 x physical media with Tails for the *Secure Viewing Station*.
 * 1 x physical media with Tails for the *Secure Viewing Station* (backup).
 
We recommend getting [16 GB Leef Supra](http://www.amazon.com/dp/B00FWQTBZ2/ref=wl_it_dp_o_pC_nS_ttl?_encoding=UTF8&colid=3NQVTBFZV73JA&coliid=IX8TE9WOYD105) USB sticks to run Tails on, and [32 GB Patriot](http://www.amazon.com/dp/B00C982KZY/ref=wl_it_dp_o_pd_nS_ttl?_encoding=UTF8&colid=3NQVTBFZV73JA&coliid=I2IJO2RQGNF7BV&psc=1) USB sticks to use when transferring files. Each journalist should have two USB sticks. For the Secure Viewing Station, we recommend getting [Corsair 64 GB](http://www.amazon.com/dp/B00EM71W1S/ref=wl_it_dp_o_pd_nS_ttl?_encoding=UTF8&colid=3NQVTBFZV73JA&coliid=I3KY4GZXC9PPV&psc=1) USB sticks.

Another alternative setup exists in which journalists do not transfer files on a USB stick, but instead use a CD-R or DVD-R. The encrypted documents are copied to the CD-R or DVD-R, then decrypted and read on the Secure Viewing Station. The disks are destroyed after first use. We recommend getting a [Samsung model burner](http://www.newegg.com/External-CD-DVD-Blu-Ray-Drives/SubCategory/ID-420) for this purpose. 

### Network firewall

An important part of SecureDrop's security model involves segmenting the infrastructure from the Internet and/or the corporate environment. For this reason, we recommend that you get:

 * 1 x firewall with pfsense and minimum three NICs.
 
We recommend getting a Netgate firewall with pfsense pre-installed, and you can choose from a firewall with [2 GB of system memory](http://store.netgate.com/NetgateAPU2.aspx) or one with [4 GB of system memory](http://store.netgate.com/APU4.aspx).
