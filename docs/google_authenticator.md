### Set up Google Authenticator for the App Server

As part of the SecureDrop installation process, you will need to set up two factor authentication using the Google Authenticator app.

On the *App Server*, open the *~/.google_authenticator* file and note the value listed on the very first line. Open the Google Authenticator app on your smartphone and follow the steps below for either iOS or Android.

**iOS instructions:**

* Select the pencil in the top-right corner
* Select the plus sign at the bottom to add a new entry
* Select *Manual Entry*
* Under *Account* enter *SecureDrop App*
* Under *Key* enter the value from the *.google_authenticator* file
* Select the option in the top-right corner to save

**Android instructions:**

* Select the menu bar in the top-right corner
* Select *Set up account*
* Select *Enter provided key* under 'Manually add an account'
* Under *Enter account name* enter *SecureDrop App*
* Under *Enter your key* enter the value from the *.google_authenticator* file
* You may leave the default type which is 'Time based'
* Select the *Add* button at the bottom to save
