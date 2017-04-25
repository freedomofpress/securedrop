Google Authenticator
====================

As part of the SecureDrop installation process, you will need to set up two
factor authentication using the Google Authenticator app for both the App and
Monitor Servers.

Connect to each of the servers using ``ssh`` and run ``google-authenticator``.
Follow the prompts, saying "yes" when prompted for a "yes/no" response. When
you've finished, open the Google Authenticator app on your smartphone and
follow the steps below for either iOS or Android. Once you've properly set up
the first server, repeat these steps again on the other.

iOS
---

- Select the pencil in the top-right corner
- Select the plus sign at the bottom to add a new entry
- Select **Scan Barcode**
- Scan the barcode using your phone's camera

A new entry will automatically be added to the list. If you wish to edit
this entry and give it a new name, do the following:

- Select the pencil in the top-right corner
- Select the pencil next to the entry you wish to edit
- Select the checkmark in the top-right corner to save

To complete the setup process, say ``y`` to each prompt presented by
``google-authenticator``.

Android
-------

- Select the menu bar in the top-right corner
- Select **Set up account**
- Select **Scan a barcode**
- Scan the barcode using your phone's camera

A new entry will automatically be added to the list. If you wish to edit
this entry and give it a new name, do the following:

- Highlight the entry with a long press
- Select the pencil in the top-right corner
- Edit the entry's name and press Save

To complete the setup process, say ``y`` to each prompt presented by
``google-authenticator``.
