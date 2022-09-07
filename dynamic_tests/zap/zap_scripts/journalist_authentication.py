# Copyright (C) 2011-2021 Mark Percival <m@mdp.im>,
# Nathan Reynolds <email@nreynolds.co.uk>, Andrey Kislyuk <kislyuk@gmail.com>,
# and PyOTP contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Zap jython uses Python 2.7.2 syntax

import time
import datetime
import hashlib
import calendar
import hmac
import base64
import unicodedata
import sys
from urllib import quote

import java.lang.String, jarray
import org.parosproxy.paros.network.HttpRequestHeader as HttpRequestHeader
import org.parosproxy.paros.network.HttpHeader as HttpHeader
from org.apache.commons.httpclient import URI


# Credentials from developer docs:
# https://docs.securedrop.org/en/stable/development/setup_development.html#using-the-docker-environment

TEST_JOURNALIST_USERNAME = "journalist"
TEST_JOURNALIST_PASSPHRASE = "correct horse battery staple profanity oil chewy"
OTP_TEST_SECRET = "JHCOGO7VCER3EJ4L"
OTP_DIGITS = 6
# OTP_INTERVAL = 30

# LOGIN_BODY_FMTSTR = "csrf_token={csrf_token}&username={username}&password={password}&token={totp}"
LOGIN_BODY_FMTSTR = "username={username}&password={password}&token={totp}"
LOGIN_URL = "https://127.0.0.1:8081/login"


def int_to_bytestring(i, padding = 8):
    result = bytearray()
    while i != 0:
        result.append(i & 0xFF)
        i >>= 8
    return bytes(bytearray(reversed(result)).rjust(padding, b'\0'))


def get_timecode(interval = 30):
    now_dtime = datetime.datetime.now()
    now = now_dtime.timetuple()
    timecode = int(time.mktime(now)) / interval
    return timecode


def get_secret_bytestring(secret):
    missing_padding = len(secret) % 8
    if missing_padding != 0:
        secret += '=' * (8 - missing_padding)
    return base64.b32decode(secret, casefold=True)


def get_str_code(code, digits = 6):
    str_code = str(code % 10 ** digits)
    while len(str_code) < digits:
        str_code = '0' + str_code
    return str_code


def generate_otp(timecode, secret, digits = 6):
    hasher = hmac.new(
        get_secret_bytestring(secret),
        int_to_bytestring(timecode),
        hashlib.sha1
    )
    hmac_hash = bytearray(hasher.digest())
    offset = hmac_hash[-1] & 0xf
    code = (
        (hmac_hash[offset] & 0x7f) << 24 |
        (hmac_hash[offset + 1] & 0xff) << 16 |
        (hmac_hash[offset + 2] & 0xff) << 8 |
        (hmac_hash[offset + 3] & 0xff)
    )
    str_code = get_str_code(code, digits)
    return str_code


def generate_totp(secret, digits = 6):
    timecode = get_timecode()
    return generate_otp(timecode, secret, digits)


def authenticate(helper, paramsValues, credentials):
	"""The authenticate function will be called for authentications made via ZAP.

	The authenticate function is called whenever ZAP requires to authenticate, for a Context for which this script was selected as the Authentication Method. The function should send any messages that are required to do the authentication and should return a message with an authenticated response so the calling method.
	NOTE: Any message sent in the function should be obtained using the 'helper.prepareMessage()' method.

	Parameters:
		helper - a helper class providing useful methods: prepareMessage(), sendAndReceive(msg)
		paramsValues - the values of the parameters configured in the Session Properties -> Authentication panel. The paramsValues is a map, having as keys the parameters names (as returned by the getRequiredParamsNames() and getOptionalParamsNames() functions below)
		credentials - an object containing the credentials values, as configured in the Session Properties -> Users panel. The credential values can be obtained via calls to the getParam(paramName) method. The param names are the ones returned by the getCredentialsParamsNames() below
	"""

	print("Authenticating via Jython script...")

    requestMethod = HttpRequestHeader.POST
    requestUri = URI("Target URL", False)
    extraPostData = paramsValues["Extra POST data"].strip()
    totp_token = generate_totp(OTP_TEST_SECRET)
    requestBody = LOGIN_BODY_FMTSTR.format(
        username=TEST_JOURNALIST_USERNAME,
        password=TEST_JOURNALIST_PASSPHRASE,
        totp=totp_token
    )
    if len(extraPostData) > 0:
        requestBody = requestBody + '&' + extraPostData
    
    msg = helper.prepareMessage()
    msg.setRequestHeader(HttpRequestHeader(requestMethod, requestUri, HttpHeader11))
    msg.setRequestBody(requestBody)

	helper.sendAndReceive(msg)

	return msg


def getRequiredParamsNames():
	"""Obtain the name of the mandatory/required parameters needed by the script.

	This function is called during the script loading to obtain a list of the names of the required configuration parameters, that will be shown in the Session Properties -> Authentication panel for configuration. They can be used to input dynamic data into the script, from the user interface (e.g. a login URL, name of POST parameters etc.)
	"""
	return jarray.array(["Target URL"], java.lang.String)


def getOptionalParamsNames():
	"""Obtain the name of the optional parameters needed by the script.

	This function is called during the script loading to obtain a list of the names of the optional configuration parameters, that will be shown in the Session Properties -> Authentication panel for configuration. They can be used to input dynamic data into the script, from the user interface (e.g. a login URL, name of POST parameters etc.).
	"""
	return jarray.array(["Extra POST data"], java.lang.String)


def getCredentialsParamsNames():
	"""Obtain the name of the credential parameters needed by the script.

	This function is called during the script loading to obtain a list of the names of the parameters that are required, as credentials, for each User configured corresponding to an Authentication using this script.
	"""
	return jarray.array([], java.lang.String)
	