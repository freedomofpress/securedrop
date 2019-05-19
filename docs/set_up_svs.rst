Set Up the *Secure Viewing Station*
===================================

The *Secure Viewing Station* is the computer where journalists read and
respond to SecureDrop submissions. Once submissions are encrypted on the
*Application Server*, only the *Secure Viewing Station* has the key to
decrypt them. The *Secure Viewing Station* is never connected to the
internet or a local network, and only ever runs from a dedicated Tails
drive. Journalists download encrypted submissions using their
*Journalist Workstation*, copy them to a *Transfer Device* (a USB
drive or a DVD) and physically transfer the *Transfer Device* to
the *Secure Viewing Station*.

Since the *Secure Viewing Station* never uses a network connection or an
internal hard drive, we recommend that you physically remove any internal
storage devices or networking hardware such as wireless cards or Bluetooth
adapters. If the machine has network ports you can't physically remove, you
should clearly cover these ports with labels noting not to use them. For an even
safer approach, fill a port with epoxy to physically disable it. We also
recommend you remove the speakers from the device (or just cut the audio cables
if that's easier). This is to prevent `exfiltration of data from the airgap via
ultrasonic audio
<https://arstechnica.com/security/2013/12/scientist-developed-malware-covertly-jumps-air-gaps-using-inaudible-sound/>`__,
which cannot be heard by humans. If you have questions about repurposing
hardware for the *Secure Viewing Station*, contact the `Freedom of the Press
Foundation <https://securedrop.org/help>`__.

You should have a Tails drive clearly labeled “SecureDrop Secure Viewing
Station”. If it's not labeled, label it right now, then boot it on the
*Secure Viewing Station*. After it loads, you should see a "Welcome to
Tails" screen, also known as the `Tails Greeter <https://tails.boum.org/doc/first_steps/startup_options/index.en.html#index2h1>`__.

Enter your passphrase to unlock the persistent storage, then press **Unlock**.
Before starting Tails, set an administration password for use with this Tails
session. To do so, click the **+** button under "Additional Settings". Click
**Administration Password** in the list of settings. Enter the password twice,
click **Add**, then click **Start Tails**.

.. note:: The Tail administration password is a one-time password. It
          is reset every time you shut down Tails. Pick a password you will be
          able to remember for the length of this session.

We will now prepare the *Secure Viewing Station*.

Ensure Filenames are Preserved
------------------------------

In order to preserve filenames when you decrypt submissions, on each *Secure
Viewing Station*, you should open a **Terminal** and type the following commands:

.. include:: includes/tails-svs-nautilus.txt

Correct the System Time
-----------------------

After booting up Tails on the *Secure Viewing Station*, you will need to
manually set the system time before you create the *SecureDrop Submission
Key*. This operation requires the Tails administration password to be set
(see above).

To set the system time:

#. Click the upper right down arrow in the menu bar and select the wrench icon:
   |select settings|
#. Then click **Date & Time**.
#. Click **Unlock**. Type in the admin password you set when you
   started up Tails.
#. Set the correct time, region and city.
#. Click **Lock**, exit Settings and wait for the system time to update in the
   top panel.

.. |select settings| image:: images/install/selectsettings.png
