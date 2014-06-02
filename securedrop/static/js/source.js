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

function is_likely_tor_browser() {
  return TBB_UAS.indexOf(window.navigator.userAgent) > -1
  && (window.navigator.mimeTypes && window.navigator.mimeTypes.length === 0);
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
          '<p>You appear to be using the Tor Browser Bundle. ' +
          'You can disable Javascript with 3 quick steps!</p>' +
          '<ol>' +
          '<li>Click the NoScript icon in the toolbar above</li>' +
          '<li>Click <img src="static/i/no16.png"/> "Forbid Scripts Globally (advised)"</li>' +
          '<li><a href="">Click here</a> to refresh the page</li>' +
          '</ol>' +
          '<p><a href="/howto-disable-js">Not using the Tor Browser Bundle?</a>'
        );
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
