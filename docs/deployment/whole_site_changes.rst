Whole Site Changes
==================

Ideally, some or all of the following changes are made to improve the
overall security of the path to the *Landing Page* and obfuscate traffic
analysis.

#. Make your entire site available through HTTPS.

   - That way, visits to your *Landing Page* won't stand out as the only encrypted
     traffic to your site.

#. Include an iframe for all (or a random subset of) visitors, loading
   this particular URL (hidden).

   - By artificially generating traffic to the endpoint it will be
     harder to distinguish these from other, 'real' requests.
   - Use a random delay for adding the iframe (otherwise the 'pairing'
     with the initial HTTP request may distinguish this traffic).

#. Print the link, URL and info block on the dead trees (the paper),
   as others have suggested.
#. Add `HSTS headers
   <http://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security>`__.

Suggested
---------

-  For publicly advertised SecureDrop instances display the Source
   Interface's Onion Service onion address on all of the organization
   public pages.
-  Mirror the Tor Browser and Tails so sources do not have to
   visit `torproject.org <https://www.torproject.org>`__ to download it.
