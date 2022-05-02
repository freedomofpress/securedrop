const TBB_UA_REGEX = /Mozilla\/5\.0 \((Windows NT 10\.0|X11; Linux x86_64|Macintosh; Intel Mac OS X 10\.[0-9]{2}|Windows NT 10\.0; Win64; x64|Android; Mobile); rv:[0-9]{2,3}\.0\) Gecko\/20100101 Firefox\/([0-9]{2,3})\.0/
const TB4A_UA_REGEX = /Mozilla\/5\.0 \(Android( [0-9]{2})?; Mobile; rv:[0-9]{2,3}\.0\) Gecko\/(20100101|[0-9]{2}\.0) Firefox\/([0-9]{2,3})\.0/;

/**
   Helper function to change display CSS property using CSS selectors
*/
function display(selector, displayStyle = "block") {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.style.display = displayStyle;
  });
}

/**
   Tor Browser always reports a UTC timezone and window dimensions
   that match the device dimensions. This is unlikely in desktop
   browsers unless they implement anti-fingerprinting techniques
   (such as Firefox privacy.resistFingerprinting).
*/
function looksLikeTorBrowser() {
  return window.navigator.userAgent.match(TBB_UA_REGEX) &&
    new Date().getTimezoneOffset() == 0 &&
    window.screen.width == window.innerWidth &&
    window.screen.height == window.innerHeight;
}

function looksLikeTorBrowserAndroid() {
    return (
        window.navigator.userAgent.match(TB4A_UA_REGEX) &&
        new Date().getTimezoneOffset() == 0
    );
};

/**
   Adds a click listener to the element with id "id", which will hide
   elementToClose.
*/
function addClose(id, elementToClose) {
  document.getElementById(id).addEventListener("click", function() {
    display(elementToClose, "none");
  });
}

/**
   If the source is using Tor Browser, encourage them to turn Tor
   Browser's Security Level to "Safest".
*/
function showSecurityLevelSuggestions() {
  display("#browser-security-level");

  // show the instruction popup when the link is clicked
  document.getElementById("disable-js").addEventListener(
    "click",
    function(e) {
      e.preventDefault();
      e.stopPropagation();
      display("#security-level-info");
    }
  );
}

function checkClearnet() {
  let url = new URL(location.href);
  // Allow localhost for development
  let localhost = ["127.0.0.1", "localhost"];
  if (localhost.indexOf(url.hostname) === -1 && !url.host.endsWith(".onion")) {
    location.href = "/tor2web-warning"
  }
}

function ready(fn) {
  if (document.readyState != "loading"){
    fn();
  } else {
    document.addEventListener("DOMContentLoaded", fn);
  }
}

ready(function() {
  if (looksLikeTorBrowser()) {
    showSecurityLevelSuggestions();
  } else if (looksLikeTorBrowserAndroid()) {
    // Warn sources if they use Tor Browser for Android
    display("#browser-android");
    addClose("browser-android-close", "#browser-android");
  } else {
    // Warn sources if they aren't using Tor Browser
    display("#browser-tb");
    addClose("browser-tb-close", "#browser-tb");
  }
  checkClearnet();
});
