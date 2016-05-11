
ready(function() {
  // Show banner warning about using Javascript
  var warning = document.querySelector('.warning');
  warning.style.display = 'block';
  document.getElementById('warning-close').addEventListener('click', function() {
    warning.style.display = 'none';
  });

  // Show disable javascript bubble if using Tor Browser
  if (is_likely_tor_browser()) {
    document.querySelector('a#disable-js').addEventListener('click', function(evt) {
      var infoBubble = document.querySelector('div.bubble');
      if (tbb_version() >= 31) {
        addClass(infoBubble, 'tbb31plus');
      }
      infoBubble.style.display = 'block';
      fadeIn(infoBubble);

      infoBubble.addEventListener('click', function() {
        infoBubble.style.display = 'none';
      });

      evt.preventDefault();
      return false; // don't follow link
    });
  }
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

function ready(fn) {
  if (document.readyState != 'loading'){
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  }
}

function fadeIn(el) {
  el.style.opacity = 0;

  var last = +new Date();
  var tick = function() {
    el.style.opacity = +el.style.opacity + (new Date() - last) / 400;
    last = +new Date();

    if (+el.style.opacity < 1) {
      (window.requestAnimationFrame && requestAnimationFrame(tick)) || setTimeout(tick, 16);
    }
  };

  tick();
}

function addClass(el, className) {
  if (el.classList) {
    el.classList.add(className);
  } else {
    el.className += ' ' + className;
  }
}
