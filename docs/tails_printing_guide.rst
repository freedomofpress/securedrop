.. _printer_setup_in_tails:

Setting Up a Printer in Tails
=============================

Because Tails is supposed to be as **amnesiac** as possible, you want to
shield your Tails stick from any extra inputs from, and outputs to, a
potentially untrusted network. This is why **we strongly recommend using
a printer that does not have WiFi or Bluetooth**, and hooking up to it
using a regular USB cable to print.

Finding a printer that works with Tails can be challenging because Tails is
based on the Linux operating system, which often has second-class hardware
support in comparison to operating systems such as Windows or macOS.

We :ref:`maintain a list of printers <printers_tested_by_fpf>` that we have
personally tested and gotten to work with Tails, in the Hardware guide; if
possible, we recommend using one of those printers. The Linux Foundation also
maintains the `OpenPrinting database <https://www.openprinting.org/printers>`_,
which documents the compatibility, or lack thereof, of numerous printers from
almost every manufacturer.

.. note:: The latest generations of printers might or might not be represented
          by the OpenPrinting database; also, the database does not document
          whether or not a printer is wireless, so this will involve manually
          checking models of interest, if you wish to use this resource as a
          guide for purchasing a non-wireless printer suitable for use with
          SecureDrop.

With that in mind, this database is arguably the best resource for researching
the compatibility of printers with Linux. As a tip for narrowing down your
search, look for printers that are compatible with Debian, or Debian-based
distributions like Ubuntu, since Tails itself is also Debian-based. This might
increase the chances for a seamless installation experience in Tails.

In any case, this document outlines the usual set of steps that we follow when
attempting to use a new printer with Tails.

.. note:: While, as of Tails 3, it's no longer necessary to have admin
   privileges in order to install or configure printers, we recommend that you
   set an admin passphrase and unlock your persistent volume; this ensures that
   the printer's installation and configuration settings persist after every
   reboot, so you don't have to reinstall it each time you start Tails.

Installing and Printing via the Tails GUI
-----------------------------------------

Let's look at Tails 3.0's typical flow for installing a USB-connected printer.
If you've enabled persistence, boot with your persistent volume, and set an
admin passphrase. Connect the printer to your Tails-booted computer via USB,
then turn the printer on.

Now, you'll want to single-click your way through **Applications** ▸
**System Tools** ▸ **Settings** ▸ **Printers**.

|select printer from settings|

In this example, we'll assume that this is the first time we've tried to install
a printer, which will show the following:

|add printer|

Click **Add a Printer**. By doing so, you'll now get a list of printers that Tails
has auto-detected. You should now see this:

|select printer to add|

In this example, we've connected an HP DeskJet F4200. Clicking on this printer
will select it for installation, which, if successful, will display the
following:

|printer installing|

This indicates that Tails is attempting to install the USB printer. Assuming you
receive no errors in this process, you will then see the following screen,
which indicates that the printer is "ready" for printing.

|printer ready|






Printing from the Command Line
------------------------------

You can also easily print from the command line using the ``lp`` command; if
you haven't already set your installed printer as default in the GUI, you can
quickly do so by adding this line to your ``~/.bashrc`` file, or entering this
directly into the terminal:

.. code:: sh

   export PRINTER=Printer-Name-Here

If you need to find the name of the printer, you can use ``lpstat`` to get a
list of installed printers, as such:

.. code:: sh

   lpstat -a

Once you've set your default printer, you can easily print from the terminal by
using the following syntax:

.. code:: sh

   lp filename.extension

While printing from the GUI is much easier, once you've got everything set up,
it's equally straightforward from the command line, if you prefer that
environment.

.. |select printer to add| image:: images/printer_setup_guide/select_printer_to_add.png
.. |select printer from settings| image:: images/printer_setup_guide/select_printer_from_settings.png
.. |printer ready| image:: images/printer_setup_guide/printer_ready.png
.. |printer installing| image:: images/printer_setup_guide/printer_installing.png
.. |add printer| image:: images/printer_setup_guide/add_printer.png
