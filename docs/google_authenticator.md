### Set up Google Authenticator for the App Server

As part of the SecureDrop installation process, you will need to set up two factor authentication using the Google Authenticator app.

Connect to the App Server using `ssh` and run `google-authenticator`. Open the Google Authenticator app on your smartphone and follow the steps below for either iOS or Android.

**iOS instructions:**

* Select the pencil in the top-right corner
* Select the plus sign at the bottom to add a new entry
* Select *Scan Barcode*
* Scan the barcode

A new entry will automatically be added to the list. If you wish to edit this entry and give it a new name, do the following:

 * Select the pencil in the top-right corner
 * Select the pencil next to the entry you wish to edit
 * Select the checkmark in the top-right corner to save
 
To complete the setup process, say `y` to each prompt presented by `google-authenticator`.

**Android instructions:**

* Select the menu bar in the top-right corner
* Select *Set up account*
* Select *Enter provided key* under 'Manually add an account'
* Under *Enter account name* enter *SecureDrop App*
* Under *Enter your key* enter the value from the *.google_authenticator* file
* You may leave the default type which is 'Time based'
* Select the *Add* button at the bottom to save
