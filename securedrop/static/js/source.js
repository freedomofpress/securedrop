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

// Warn about using JavaScript and not using Tor Browser
$(function(){
  if (is_likely_tor_browser()) {
    // If the source is using Tor Browser, we want to encourage them to turn Tor
    // Browser's Security Slider to "High", which enables various hardening
    // methods, including disabling JavaScript. Since JS is disabled by turning
    // the Security Slider to "High", this code only runs if it set to another
    // (less hardened) setting.
    $('.js-warning').show();
    $('#js-warning-close').click(function(){
      $('.js-warning').hide(200);
    });

    // Display a friendly bubble with step-by-step instructions on how to turn
    // the security slider to High.
    var infoBubble = $('#security-slider-info-bubble');
    var fadeDuration = 500; // milliseconds

    $('#disable-js').click(function() {
      infoBubble.fadeIn(fadeDuration);
      return false; // don't follow link
    });

    // If the user clicks outside of the infoBubble while it is visible, hide it.
    $(window).click(function() {
      if (infoBubble.is(':visible')) {
        infoBubble.fadeOut(fadeDuration);
      }
    });

    // If the user clicks inside the infoBubble while it is visible, make sure
    // it stays visible.
    infoBubble.click(function(e) {
      e.stopPropagation();
    });
  } else {
    // If the user is not using Tor Browser, we want to encourage them to do so.
    $('.use-tor-browser').show();
    $('.hide-if-not-tor-browser').hide();
    $('#use-tor-browser-close').click(function(){
      $('.use-tor-browser').hide(200);
    });
  }
});
