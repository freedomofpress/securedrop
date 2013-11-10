var TBB_UAS = [
    "Mozilla/5.0 (Windows NT 6.1; rv:10.0) Gecko/20100101 Firefox/10.0",
    "Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0",
];

function is_likely_tor_browser() {
    return TBB_UAS.indexOf(window.navigator.userAgent) > -1
        && (window.navigator.mimeTypes && window.navigator.mimeTypes.length === 0);
}

function warn_user(messageDiv) {
    var messageDiv = $('<div id="warning_text">')
	.html('<b>WARNING:</b>Your browser currently has Javascript enabled.' +
	      '<a id="disable-js-anchor" href="/howto-disable-js">Click here</a>' +
	      'to learn how. Or click on this warning to continue. <strong>We recommend' +
	      'disabling Javascript to protect your anonymity. </strong>');

    var warningDiv = $('<div id="warning">')
	.append(messageDiv);

    $('#warning').remove();
    $(document.body).append(warningDiv);
    warningDiv.fadeIn(1000);
}

$(window).load(function() {
    warn_user();
    if (is_likely_tor_browser())
	$("#disable-js-anchor").click(function() {
	    $('#warning').remove();
	    var infoP = $('<p class="bubble">')
		.html('<img id="" src=""/>You appear to be using the Tor Browser Bundle.' +
		      'You can disable Javascript with 3 quick steps!</p>' +
		      '<div style="width:75%;margin:0 auto;padding-bottom:1em;">' +
		      '<ol><li>Click the NoScript icon in the toolbar above</li>' +
		      '<li>Click on <img src="static/i/no16.png"/> "Forbid Scripts Globally (advised)"</li>' +
		      '<li>Refresh this page</li>' +
		      '</ol></div><p><a href="/howto-disable-js">Not using the Tor Browser Bundle?</a>');
	    
	    $(document.body).append(infoP);
	    infoP.fadeIn(1000);
	    infoP.click(function() {
		infoP.remove();
	    });
	    return false; // don't follow link
	});
});

	    