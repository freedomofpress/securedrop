// Warn about using Javascript
$(function(){
  $('.warning').show();
  $('#warning-close').click(function(){
    $('.warning').hide(200);
  });
});

// Customized, super-easy instructions for disabling JS in TBB
var TBB_UAS = [
  "Mozilla/5.0 (Windows NT 6.1; rv:10.0) Gecko/20100101 Firefox/10.0",
  "Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0",
  "Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0",
];

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

$(function() {
  if (is_likely_tor_browser()) {
    $("a#disable-js").click(function() {
      // Toggle the bubble if it already exists
      var infoBubble = $("p.bubble");
      if (infoBubble.length > 0) {
        infoBubble.toggle();
      } else {
        var infoBubble = $('<p class="bubble">').html(
          '<p>You appear to be using the Tor Browser. ' +
          'You can disable Javascript in 3 easy steps!</p>' +
          '<ol>' +
          '<li>Click the <img src="static/i/no16.png"> NoScript icon in the toolbar above</li>' +
          '<li>Click <strong><img src="static/i/no16-global.png"/> Forbid Scripts Globally (advised)</strong></li>' +
          '<li>If the page does not refresh automatically, <a href="">click here</a> to refresh the page</li>' +
          '</ol>' +
          '<p><a href="/howto-disable-js">Not using the Tor Browser Bundle?</a>'
        );
        if (tbb_version() >= 31) {
          infoBubble.addClass("tbb31plus");
        }
        $(document.body).append(infoBubble);
        infoBubble.fadeIn(500);
        infoBubble.click(function() {
          infoBubble.toggle();
        });
      }
      return false; // don't follow link
    });
  }
});
