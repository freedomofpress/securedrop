// Warn about using Javascript and not using Tor Browser
$(function(){
  if (is_likely_tor_browser()) {
    $('.js-warning').show();
    $('#js-warning-close').click(function(){
      $('.js-warning').hide(200);
    });
  }
  else {
    $('.use-tor-browser').show();
    $('#use-tor-browser-close').click(function(){
      $('.use-tor-browser').hide(200);
    });
  }
});

var TBB_UA_REGEX = /Mozilla\/5\.0 \(Windows NT 6\.1; rv:[0-9]{2}\.0\) Gecko\/20100101 Firefox\/([0-9]{2})\.0/;

function is_likely_tor_browser() {
  return window.navigator.userAgent.match(TBB_UA_REGEX) &&
         (window.navigator.mimeTypes &&
          window.navigator.mimeTypes.length === 0);
}

function tbb_version() {
  var ua_match = window.navigator.userAgent.match(TBB_UA_REGEX);
  var major_version = ua_match[1];
  return Number(major_version);
}

// Display a friendly bubble to explain how to turn the security slider to High
// if the source is using Tor Browser with JS enabled
$(function() {
  if (is_likely_tor_browser()) {
    $("a#disable-js").click(function() {
      // Toggle the bubble if it already exists
      var infoBubble = $("div.bubble");
      if (tbb_version() >= 31) {
        infoBubble.addClass("tbb31plus");
      }
      infoBubble.fadeIn(500);
      infoBubble.click(function() {
        infoBubble.toggle();
      });
      return false; // don't follow link
    });
  }
});
