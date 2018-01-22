function setUserAgent(userAgent) {
  window.navigator.__defineGetter__('userAgent', function () {
	  return userAgent;
  });
}

function setMimeTypes(mimeTypes) {
  window.navigator.__defineGetter__('mimeTypes', function () {
    return mimeTypes
  });
}

SAFARI_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7"
FIREFOX_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:57.0) Gecko/20100101 Firefox/57.0"
TOR_BROWSER_UA = "Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0"

QUnit.test("is_likely_tor_browser: Returns falsey value for Safari User Agent", function( assert ) {
  var originalUserAgent = window.navigator.userAgent;
  setUserAgent(SAFARI_UA);

  assert.deepEqual(is_likely_tor_browser(), null);

  setUserAgent(originalUserAgent);
});

QUnit.test("is_likely_tor_browser: Returns falsey value for Firefox User Agent", function( assert ) {
  var originalUserAgent = window.navigator.userAgent;
  setUserAgent(FIREFOX_UA);

  assert.deepEqual(is_likely_tor_browser(), null);

  setUserAgent(originalUserAgent);
});

QUnit.test("is_likely_tor_browser: Returns true for Tor Browser User Agent", function( assert ) {
  var originalUserAgent = window.navigator.userAgent;
  setUserAgent(TOR_BROWSER_UA);
  var originalMimeTypes = window.navigator.mimeTypes;
  // Tor Browser has window.navigator.mimeTypes set to empty array for anonymity
  setMimeTypes([]);

  assert.deepEqual(is_likely_tor_browser(), true);

  setUserAgent(originalUserAgent);
  setMimeTypes(originalMimeTypes);
});
