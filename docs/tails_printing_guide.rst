Setting up a printer with Tails
===============================

Because Tails is supposed to be as "amnesiac" as possible, you want to
shield your Tails stick from any extra inputs from, and outputs to, a
potentially untrusted network. This is why **we strongly recommend using
a printer that does not have WiFi or Bluetooth**, and hooking up to it
using a regular USB cable to print.

Normally, any printer should work with Tails "out of the box." Most
difficulties stem from not selecting the right driver (extra software
needed for the printer and computer to communicate). Luckily, Tails has
a large number of drivers for just about any popularly manufactured
printer on hand, without even having to download new drivers from the
web.

Boot up Tails with both your persistent volume, and set an admin passphrase.

.. todo:: Consider adding images of enabling persistence and setting an admin
          passphrase when starting Tails.

Make sure your computer is NOT connected to the internet. This will make
sure that your printer set-up is never influenced by a network
connection.

|no network connection required|

Plug in your printer and navigate to Printing. "Applications -> System
Tools -> Administration -> Printing". You will need to authenticate this
action with the admin passphrase you set when booting up Tails.

|navigate to Printing|

|grant admin|

Click **Add**.

|add new printer|

Immediately, Tails will recongize the plugged-in printer, and make the
best suggestion from its on-board database of printer drivers.

|searching for drivers...|

Tails will guide you through a default set-up, suggesting the best match
for the printer you have. These choices come from Tails' pre-installed
driver database.

|default set up 1|

|default set up 2|

The recommended driver does not always match the actual make and model
of your printer, but starting with the recommendations is a good idea.
Sometimes you get lucky, and Tails suggests a perfect match. Click
**Forward**, and **Apply** your settings.

|apply settings|

You'll notice that the printer is now listed in your Printing
Configurations in your persistent storage.

|add your printer|

The only way to be sure you have the right driver is by doing a test
print. Right-click on your new printer config and select **Properties** to
open its settings, then click **Print Test Page**.

|select "Properties"|

|print a test page|

In this initial test, the recommended driver was wrong! My test page
came out garbled, and my printer gave me a warning that I had to
manually clear before the page printed.

|garbled test print|

|warning light indicator|

Don't worry if this happens to you; you can edit the printer
configuration to point it to the correct driver for your model. Select
**Properties** again and choose **Change...** next to the "Make and Model"
directive.

|change make and model|

To fix this problem, I selected the CUPS + Gutenprint driver, even
though it wasn't recommended. Click **Forward** to save your changes.

|custom choice for make and model|

Do another test print, checking your printer for indicators that it's
working or not. This time, printing works perfectly. If you still
experience garbled text, try another driver from your selections. It is
a process of trial-and-error.

|perfect test print|

.. |no network connection required| image:: images/printer_setup_guide/tails_desktop_no_network.png
.. |navigate to Printing| image:: images/printer_setup_guide/path_to_printer_settings.png
.. |grant admin| image:: images/printer_setup_guide/grant_admin.png
.. |add new printer| image:: images/printer_setup_guide/printer_list.png
.. |searching for drivers...| image:: images/printer_setup_guide/searching_for_drivers.png
.. |default set up 1| image:: images/printer_setup_guide/driver_search_result_default_1.png
.. |default set up 2| image:: images/printer_setup_guide/driver_search_result_default_2.png
.. |apply settings| image:: images/printer_setup_guide/save_printer_config.png
.. |add your printer| image:: images/printer_setup_guide/printer_config_added.png
.. |select "Properties"| image:: images/printer_setup_guide/edit_properties.png
.. |print a test page| image:: images/printer_setup_guide/print_test_page.png
.. |garbled test print| image:: images/printer_setup_guide/bad_test_page.png
.. |warning light indicator| image:: images/printer_setup_guide/unhappy_printer.png
.. |change make and model| image:: images/printer_setup_guide/change_make_and_model.png
.. |custom choice for make and model| image:: images/printer_setup_guide/driver_search_results_custom.png
.. |perfect test print| image:: images/printer_setup_guide/good_test_page.png
