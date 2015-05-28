### Set up Google Authenticator

As part of the SecureDrop installation process, you will need to set up two factor authentication for both servers using the Google Authenticator app.

Connect to the *Application Server* using `ssh` and run `google-authenticator`. Open the Google Authenticator app on your smartphone and follow the steps below for either iOS or Android. Repeat these steps for the *Monitor Server*.

**iOS instructions:**

* Select the pencil in the top-right corner
* Select the plus sign at the bottom to add a new entry
* Select *Scan Barcode*
* Scan the barcode using your phone's camera

A new entry will automatically be added to the list. If you wish to edit this entry and give it a new name, do the following:

 * Select the pencil in the top-right corner
 * Select the pencil next to the entry you wish to edit
 * Select the checkmark in the top-right corner to save

To complete the setup process, say `y` to each prompt presented by `google-authenticator`.

**Android instructions:**

* Select the menu bar in the top-right corner
* Select *Set up account*
* Select *Scan a barcode*
* Scan the barcode using your phone's camera

A new entry will automatically be added to the list. If you wish to edit this entry and give it a new name, do the following:

* Highlight the entry with a long press
* Select the pencil in the top-right corner
* Edit the entry's name and press Save

To complete the setup process, say `y` to each prompt presented by `google-authenticator`.
