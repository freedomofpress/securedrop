How To Use SecureDrop As A Source
=================================

SecureDrop Depends on the Tor Browser
-------------------------------------

Sources submitting documents or messages to SecureDrop must connect to
the SecureDrop Interface using the Tor network, free software that makes
users' internet activity much more difficult to trace. The easiest and
most secure way to use Tor is to download the Tor Browser Bundle from
https://www.torproject.org/. This bundle installs the Tor browser, as
well as an application that is used to connect to the Tor network.

The Tor Browser can be used to access Tor *hidden service URLs*, which
have domain names that end in ".onion". Media organizations will provide
links to the .onion URLs of their SecureDrop pages, and we `maintain a
list <https://freedom.press/securedrop/directory>`__ of official pages
as well. Sources can and should use the `Tails operating
system <https://tails.boum.org>`__ for a higher level of security.

Using SecureDrop As a Source
----------------------------

Open the Tor Browser and navigate to the .onion hidden service URL
provided by the media organization whose SecureDrop page you would like
to visit. The page should look similar to the screenshot below. If this
is the first time you're using the Tor browser, it's likely that you
have Javascript enabled. If you do, you will see the red warning below
which will explain that this is a security risk. If you don't have
Javascript enabled, you can skip the next step.

|Javascript warning|

Click the ``Learn how to disable it`` link on the Javascript warning and
a message will pop up explaining how to disable Javascript. Follow the
instructions and refresh the page if it does not happen automatically.

|Fix Javascript warning|

The page should now look similar to the screenshot below. If this is the
first time you are using SecureDrop, click the ``Submit Documents``
button.

|Source Interface|

You should now see a screen that shows the unique codename that
SecureDrop has generated for you. In the example screenshot below the
codename is ``sink los radium bcd nab privy nadir``, but yours will be
different. It is extremely important that you both remember this code
and keep it secret. After submitting documents, you will need to provide
this code to log back in and check for responses.

The best way to protect your codename is to memorize it. If you cannot
memorize it right away, we recommend writing it down and keeping it in a
safe place at first, and gradually working to memorize it over time.
Once you have memorized it, you should destroy the written copy.

SecureDrop allows you to choose the length of your codename, in case you
want to create a longer codename for extra security. Once you have
generated a codename and put it somewhere safe, click ``Continue``.

|Memorizing your codename|

You will next be brought to the submission interface, where you may
upload a document, enter a message to send to journalists, or both. You
can only submit one document at a time, so you may want to combine
several files into a zip archive if necessary. The maximum submission
size is currently 500MB. If the files you wish to upload are over that
limit, we recommend that you send a message to the journalist explaining
this, so that they can set up another method for transferring the
documents.

When your submission is ready, click ``Submit``.

|Submit a document|

After clicking ``Submit``, a confirmation page should appear, showing
that your message and/or documents have been sent successfully. On this
page you can make another submission or view responses to your previous
messages.

|Confirmation page|

If you have already submitted a document and would like to check for
responses, click the ``Check for a Response`` button on the media
organization's SecureDrop homepage.

|Source Interface|

The next page will ask for your secret codename. Enter it and click
``Continue``.

|Check for response|

If a journalist has responded, his or her message will appear on the
next page. This page also allows you to upload another document or send
another message to the journalist. Be sure to delete any messages here
before navigating away.

|Check for a reply|

After you delete the message from the journalist, make sure you see the
below message.

|Delete received messages|

If the server experiences a large number of new sources signing up at
once and is overloaded with submissions, the journalist will flag your
message on their end and you will see the message below. They can't
write a reply to you until you've seen this message for security
reasons. This will only happen the first time a journalist replies and
with subsequent replies you will skip this step. Click ``Refresh`` or
log in again to see if a journalist has responded.

|Check for an initial response|

Repeat these steps to continue communicating with the journalist.

.. |Javascript warning| image:: /docs/images/manual/source-step1.png
.. |Fix Javascript warning| image:: /docs/images/manual/source-step2.png
.. |Source Interface| image:: /docs/images/manual/source-step3-and-step7.png
.. |Memorizing your codename| image:: /docs/images/manual/source-step4.png
.. |Submit a document| image:: /docs/images/manual/source-step5.png
.. |Confirmation page| image:: /docs/images/manual/source-step6.png
.. |Check for response| image:: /docs/images/manual/source-step8.png
.. |Check for a reply| image:: /docs/images/manual/source-step9.png
.. |Delete received messages| image:: /docs/images/manual/source-step10.png
.. |Check for an initial response| image:: /docs/images/manual/source_flagged_for_reply.png
