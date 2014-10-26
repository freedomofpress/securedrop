# How to Use SecureDrop

## SecureDrop Depends on the Tor Browser

Sources submitting documents or messages to SecureDrop, and the journalists viewing this correspondence, must connect to the respective Source or Document Interface using the Tor network, free software that makes users' internet activity much more difficult to trace. The easiest and most secure way to use Tor is to download the Tor Browser Bundle from https://www.torproject.org/. This bundle installs the Tor browser, as well as an application that is used to connect to the Tor network.

The Tor Browser can be used to access Tor _hidden service URLs_, which have domain names that end in ".onion". Media organizations will provide links to the .onion URLs of their SecureDrop pages, and we [maintain a list](https://freedom.press/securedrop/directory) of official pages as well. Each journalist that uses SecureDrop connects to the service with his or her own personal .onion URL.

## Using SecureDrop As a Source

Open the Tor Browser and navigate to the .onion hidden service URL provided by the media organization whose SecureDrop page you would like to visit. The page should look similar to the screenshot below. If this is the first time you're using the Tor browser, it's likely that you have Javascript enabled. If you do, you will see the red warning below which will explain that this is a security risk. If you don't have Javascript enabled, you can skip the next step.

![Javascript warning](/docs/images/manual/source_landing_with_warning.png)

Click the `Click here` link on the Javascript warning and a message will pop up explaining how to disable Javascript. Follow the instructions and refresh the page if it does not happen automatically.

![Fix Javascript warning](/docs/images/manual/source_landing_page_disable_javascript.png)

The page should now look similar to the screenshot below. If this is the first time you are using SecureDrop, click the `Submit Documents` button.

![Source Interface](/docs/images/manual/source_landing_page_no_warning.png)

You should now see a screen that shows the unique codename that SecureDrop has generated for you. In the example screenshot below the codename is `vail icky aires proud peale menu adair`, but yours will be different. It is extremely important that you both remember this code and keep it secret. After submitting documents, you will need to provide this code to log back in and check for responses.

The best way to protect your codename is to memorize it. If you cannot memorize it right away, we recommend writing it down and keeping it in a safe place at first, and gradually working to memorize it over time. Once you have memorized it, you should destroy the written copy.

SecureDrop allows you to choose the length of your codename, in case you want to create a longer codename for extra security. Once you have generated a codename and put it somewhere safe, click `Continue`.

![Memorizing your codename](/docs/images/manual/source_generate_codename.png)

You will next be brought to the submission interface, where you may upload a document, enter a message to send to journalists, or both. You can only submit one document at a time, so you may want to combine several files into a zip archive if necessary. The maximum submission size is currently 500MB. If the files you wish to upload are over that limit, we recommend that you send a message to the journalist explaining this, so that they can set up another method for transferring the documents. 

When your submission is ready, click `Submit`.

![Submit a document](/docs/images/manual/source_upload_submission.png)

After clicking `Submit`, a confirmation page should appear, showing that your message and/or documents have been sent successfully. On this page you can make another submission or view responses to your previous messages.

![Confirmation page](/docs/images/manual/source_submission_received.png)

If you have already submitted a document and would like to check for responses, click the `Check for a Response` button on the media organization's SecureDrop homepage.

![Source Interface](/docs/images/manual/source_landing_page_no_warning.png)

The next page will ask for your secret codename. Enter it and click `Continue`.

![Check for response](/docs/images/manual/source_second_login.png)

If a journalist wishes to reply to you, they will flag your message on their end and you will see the message below. They can't write a reply to you until you've seen this message for security reasons. This will only happen the first time a journalist replies and with subsequent replies you will skip this step.

![Check for an initial response](/docs/images/manual/source_flagged_for_reply.png)

Click `Refresh` or log in again. If a journalist has responded, his or her message will appear on the next page. This page also allows you to upload another document or send another message to the journalist. Be sure to delete any messages here before navigating away.

![Check for a real response](/docs/images/manual/source_reply_from_journalist.png)

After you delete the message from the journalist, make sure you see the below message.

![Delete received messages](/docs/images/manual/source_reply_deleted.png)

Repeat to continue communicating with the journalist.