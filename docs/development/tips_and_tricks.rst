Tips & Tricks
=============

Using Tor Browser with the development environment
--------------------------------------------------

We strongly encourage sources to use the Tor Browser when they access
the Source Interface. Tor Browser is the easiest way for the average
person to use Tor without making potentially catastrophic mistakes,
makes disabling Javascript easy via the handy NoScript icon in the
toolbar, and prevents state about the source's browsing habits
(including their use of SecureDrop) from being persisted to disk.

Since Tor Browser is based on an older version of Firefox (usually the
current ESR release), it does not always render HTML/CSS the same as
other browsers (especially more recent versions of browsers). Therefore,
we recommend testing all changes to the web application in the Tor
Browser instead of whatever browser you normally use for web
development. Unfortunately, it is not possible to access the local
development servers by default, due to Tor Browser's proxy
configuration.

To test the development environment in Tor Browser, you need to add an
exception to allow Tor Browser to access localhost:

#. Open the "Tor Browser" menu and click "Preferences..."
#. Choose the "Advanced" section and the "Network" subtab under it
#. In the "Connection" section, click "Settings..."
#. In the text box labeled "No Proxy for:", enter ``127.0.0.1``

   -  Note: for some reason, ``localhost`` doesn't work here.

#. Click "Ok" and close the Preferences window

You should now be able to access the development server in the Tor
Browser by navigating to ``127.0.0.1:8080`` and ``127.0.0.1:8081``.
