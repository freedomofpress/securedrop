const TBB_UA_REGEX = /Mozilla\/5\.0 \((Windows NT 10\.0|X11; Linux x86_64|Macintosh; Intel Mac OS X 10\.14|Windows NT 10\.0; Win64; x64); rv:[0-9]{2}\.0\) Gecko\/20100101 Firefox\/([0-9]{2})\.0/;
const ORFOX_UA_REGEX = /Mozilla\/5\.0 \(Android; Mobile; rv:[0-9]{2}\.0\) Gecko\/20100101 Firefox\/([0-9]{2})\.0/;

function fadeIn(el, duration = 200, displayStyle = "block") {
  const frameDuration = 16;
  let steps = duration / frameDuration;
  let startingOpacity = Number.parseFloat(getComputedStyle(el).opacity);
  let opacityStep = Math.max(0.001, (1 - startingOpacity) / steps);
  let tick = function() {
    let currentOpacity = Number.parseFloat(getComputedStyle(el).opacity);
    el.style.display = displayStyle;
    if (currentOpacity < 1) {
      el.style.opacity = currentOpacity + opacityStep;
      requestAnimationFrame(tick);
    }
  };

  tick();
}

function fadeOut(el, duration = 200) {
  const frameDuration = 16;
  let steps = duration / frameDuration;
  let startingOpacity = Number.parseFloat(getComputedStyle(el).opacity);
  let opacityStep = Math.max(0.001, startingOpacity / steps);
  let tick = function() {
    let currentOpacity = Number.parseFloat(getComputedStyle(el).opacity);
    if (currentOpacity > 0) {
      el.style.opacity = currentOpacity - opacityStep;
      requestAnimationFrame(tick);
    } else {
      el.style.display = "none";
    }
  };

  tick();
};

function hide(selector) {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.style.display = "none";
    element.classList.add("hidden");
  });
}

function show(selector, displayStyle = "block") {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.style.display = displayStyle;
    element.classList.remove("hidden");
  });
}

/**
   Adds a click listener to the element with id "id", which will fade
   and hide elementToClose.
*/
function addFadingClose(id, elementToClose, fadeDuration = 200) {
  document.getElementById(id).addEventListener("click", function() {
    fadeOut(elementToClose, fadeDuration);
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

function looksLikeOrfox() {
    return (
        window.navigator.userAgent.match(ORFOX_UA_REGEX) &&
        new Date().getTimezoneOffset() == 0
    );
};

/**
   If the source is using Tor Browser, encourage them to turn Tor
   Browser's Security Setting to "Safest".
*/
function showTorSuggestions() {
  show("#js-warning");

  let infoBubble = document.getElementById("security-setting-info");

  // show the instruction popup when the link is clicked
  document.getElementById("disable-js").addEventListener(
    "click",
    function(e) {
      e.preventDefault();
      e.stopPropagation();
      fadeIn(infoBubble);
    }
  );
}

/**
   Show Orfox-specific suggestions.
*/
function showOrfoxSuggestions() {
  hide(".hide-if-not-tor-browser");
  let orfoxBrowser = document.getElementById("orfox-browser");
  show("#orfox-browser");
  addFadingClose("orfox-browser-close", orfoxBrowser);
}

/**
   If the user is not using a Tor browser, suggest it.
*/
function suggestTor() {
  hide(".hide-if-not-tor-browser");
  let useTorBrowser = document.getElementById("use-tor-browser");
  useTorBrowser.style.display = "block";
  addFadingClose("use-tor-browser-close", useTorBrowser);
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
    showTorSuggestions();
  } else {
    if (looksLikeOrfox()) {
      showOrfoxSuggestions();
    } else {
      suggestTor();
    }
  }
});
