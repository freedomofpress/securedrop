var TBB_UAS = [
    "Mozilla/5.0 (Windows NT 6.1; rv:10.0) Gecko/20100101 Firefox/10.0",
    "Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0",
];
function is_likely_tor_browser() {
    return TBB_UAS.indexOf(window.navigator.userAgent) > -1
        && (window.navigator.mimeTypes && window.navigator.mimeTypes.length === 0);
}

// TODO: rewrite using JQuery
window.addEventListener('load', function showJSWarning() {
    var dim_div = document.createElement('div');
    dim_div.id = 'js-warning-dim';
    document.body.appendChild(dim_div);

    var warning_div = document.createElement('div');
    warning_div.className = "center";
    warning_div.innerHTML = '<h1>Warning!</h1><p>Your browser currently has Javascript enabled. <strong>We recommend disabling Javascript to protect your anonymity.</strong></p>';
    if (is_likely_tor_browser()) {
        warning_div.id = 'js-warning-tbb';
        warning_div.innerHTML += '<p>You appear to be using the Tor Browser Bundle. You can disable Javascript with 3 quick steps!</p><ol><li>Click the NoScript icon in the toolbar above</li><li>Click "Forbid Scripts Globally (advised)"</li><li>Refresh this page</li></ol><p><a href="/howto-disable-js">Not using the Tor Browser Bundle?</a></p>';
    } else {
        warning_div.id = 'js-warning-no-tbb';
        warning_div.innerHTML += '<p><a href="/howto-disable-js">Click here</a> to learn how.</p>';
    }
    document.body.appendChild(warning_div);
});
