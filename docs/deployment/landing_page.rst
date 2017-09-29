.. _Landing Page:

Landing Page
============

URL and location
----------------

Ideally you would not use a separate subdomain, but would use a path at
your top-level domain, e.g. organization.com/securedrop. This is because
TLS does not encrypt the hostname, so a SecureDrop user whose connection
is being monitored would be trivially discovered.

If the landing page is deployed on the same domain as another site, you
might consider having some specific configuration (such as the security
headers below) apply only to the /securedrop request URI. This can be done
in Apache by the encapsulating these settings within a
`<Location> <https://httpd.apache.org/docs/2.4/mod/core.html#location>`__
block, which can be defined similarly in nginx by using the
`location {} <http://nginx.org/en/docs/http/ngx_http_core_module.html#location>`__
directive.

HTTPS only (no mixed content)
-----------------------------

Most news organizations, `in fact almost
all <https://freedom.press/blog/2014/09/after-nsa-revelations-why-arent-more-news-organizations-using-https>`__,
do not use HTTPS encryption by default. This is the number one minimum
requirement for the SecureDrop landing page on your website. Without
HTTPS, a source can easily be exposed as a visitor to your site.

This may be difficult if your website serves advertisements or utilizes
a legacy content delivery network. You should make sure the SecureDrop
landing page does not serve ads of any kind, even if the rest of your
site does.

If you do not serve ads on any of your site, you should also consider
switching your whole site over to HTTPS by default immediately. If you
do serve ads, consider pressuring your ad networks to enable you to
switch to HTTPS for your entire website in the future.

If your website needs to operate in both HTTPS and HTTP mode, use
protocol-relative URLs for resources such as images, CSS and JavaScript
in common templates to ensure your page does not end up in a mixed
HTTPS/HTTP state.

Consider submitting your domain to be included in the `Chrome HSTS
preload list <https://hstspreload.appspot.com/>`__ if you can meet all
of the requirements. This will tell web browsers that the site is only
ever to be reached over HTTPS.

Perfect Forward Secrecy
-----------------------

Perfect Forward Secrecy (PFS) is a property of encryption protocols that
ensures each SSL session has a unique key, meaning that if the key is
compromised in the future it can't be used to decrypt previously
recorded SSL sessions. You may need to talk to your CA (certificate
authority) and CDN (content delivery network) for this, although our
recommended configuration below provides forward secrecy.

SSL certificate recommendations
-------------------------------

Regardless of where you choose to purchase your SSL cert and which CA
issues it, you'll often be asked to generate the private key and a CSR
(certificate signing request).

When you do this, it's imperative that you use SHA-2 as the hashing
algorithm instead of SHA-1, which is `being phased
out <http://googleonlinesecurity.blogspot.com/2014/09/gradually-sunsetting-sha-1.html>`__.
You should also choose a key size of *at least* 2048 bits. These
parameters will help ensure that the encryption used on your landing
page is sufficiently strong. The following example OpenSSL command will
create a private key and CSR with a 4096-bit key length and a SHA-256
signature:

::

    openssl req -new -newkey rsa:4096 -nodes -sha256 -keyout domain.com.key -out domain.com.csr

**Don't load any resources (scripts, web fonts, etc.) from 3rd parties
(e.g. Google Web Fonts)**

This will potentially leak information about sources to third parties,
which can more easily be accessed by law enforcement agencies. Simply
copy them to your server and serve them yourself to avoid this problem.

Don't use 3rd party analytics, tracking, or advertising
-------------------------------------------------------

Most news websites, even those that are non-profits, use 3rd-party
analytics tools or tracking bugs on their websites. It is vital that
these are disabled for the SecureDrop landing page.

In the past, some news organizations were heavily criticized when launching
their SecureDrop instances because their landing page contained
trackers. They claimed they were going to great lengths to protect
sources' anonymity, but by having trackers on their landing page, this also
opened up multiple avenues for third parties to collect information on
those sources. This information can potentially be accessed by law
enforcement or intelligence agencies and could unduly expose a source.

Similarly, consider avoiding the use of Cloudflare (and other CDNs: Akamai, StackPath, Incapsula, Amazon CloudFront, etc.) for the SecureDrop landing page. These services intercept requests between a potential source and the SecureDrop landing page and can be used to `track <https://github.com/Synzvato/decentraleyes/wiki/Frequently-Asked-Questions>`__ or collect information on sources.

Apply applicable security headers
---------------------------------

Security headers give instructions to the web browser on how to handle
requests from the web application. These headers set strict rules for
the browser and help mitigate against potential attacks. Given the
browser is a main avenue for attack, it is important these headers are
as strict as possible.

You can use the site
`securityheaders.com <https://securityheaders.com>`__ to easily test
your website's security headers.

If you use Apache, you can use these:

::

    Header set Cache-Control "max-age=0, no-cache, no-store, must-revalidate"
    Header edit Set-Cookie ^(.*)$ $;HttpOnly
    Header set Pragma "no-cache"
    Header set Expires "-1"
    Header always append X-Frame-Options: DENY
    Header set X-XSS-Protection: "1; mode=block"
    Header set X-Content-Type-Options: nosniff
    Header set X-Download-Options: noopen
    Header set X-Permitted-Cross-Domain-Policies: master-only
    Header set Content-Security-Policy: "default-src 'self'"

If you intend to run nginx as your webserver instead, this will work:

::

    add_header Cache-Control "max-age=0, no-cache, no-store, must-revalidate";
    add_header Pragma no-cache;
    add_header Expires -1;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options nosniff;
    add_header Content-Security-Policy "default-src 'self'";
    add_header X-Download-Options: noopen;
    add_header X-Permitted-Cross-Domain-Policies master-only;


Additional Apache configuration
-------------------------------

To enforce HTTPS/SSL always, you need to set up redirection within the
HTTP (port 80) virtual host:

::

    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule (.*) https://%{HTTP_HOST}%{REQUEST_URI}

The same thing can be achieved in nginx with a single line:

::

    return 301 https://$server_name$request_uri;

In your SSL (port 443) virtual host, set up HSTS and use these settings
to give preference to the most secure cipher suites:

::

    Header set Strict-Transport-Security "max-age=16070400;"
    SSLProtocol all -SSLv2 -SSLv3
    SSLHonorCipherOrder on
    SSLCompression off
    SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH

Here's a similar example for nginx:

::

    add_header Strict-Transport-Security max-age=16070400;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";

.. note:: We have prioritized security in selecting these cipher suites, so if
          you choose to use them then your site might not be compatible with
          legacy or outdated browsers and operating systems. For a good
          reference check out `Cipherli.st <https://cipherli.st/>`__.

You'll need to run ``a2enmod headers ssl rewrite`` for all these to
work. You should also set ``ServerSignature Off`` and
``ServerTokens Prod``, typically in /etc/apache2/conf.d/security. For nginx,
use ``server_tokens off;`` so that the webserver doesn't leak extra information.

If you use nginx, `you can follow this
link <https://gist.github.com/mtigas/8601685>`__ and use the
configuration example provided by ProPublica.

**Change detection monitoring for the web application configuration and
landing page content**

OSSEC is a free and open source host-based intrusion detection suite
that includes a file integrity monitor. More information can be found
`here. <https://ossec.github.io/>`__

**Don't log access to the landing page in the webserver**

Here's an Apache example that would exclude the landing page from
logging:

::

    SetEnvIf Request_URI "^/securedrop$" dontlog
    CustomLog logs/access_log common env=!dontlog

In nginx, logging can be disabled like so:

::

    access_log off;
    error_log off;

**Security suggestions**

To guard your landing page against being modified by an attacker and
directing sources to a rogue SecureDrop instance, you will need good
security practices applying to the machine where it is hosted. Whether
it's a VPS in the cloud or dedicated server in your office, you should
consider the following:

-  Brute force login protection (see sshguard or fail2ban)
-  Disable root SSH login
-  Use SSH keys instead of passwords
-  Use long, random and complex passwords
-  Firewall rules to restrict accessible ports (see iptables or ufw)
-  AppArmor, grsecurity, SELINUX, modsecurity
-  Intrusion and/or integrity monitoring (see Logwatch, OSSEC, Snort,
   rkhunter, chkrootkit)
-  Downtime alerts (Nagios or Pingdom)
-  Two-factor authentication (see libpam-google-authenticator,
   libpam-yubico)

It's preferable for the landing page to have its own segmented
environment instead of hosting it alongside other sites running
potentially vulnerable software or content management systems. Check
that user and group file permissions are locked down and that modules or
gateway interfaces for dynamic scripting languages are not enabled. You
don't want any unnecessary code or services running as this increases
the attack surface.
