"""
This script can be used by the Script Based Authentication Method to perform authentication for a given context.

To use this script, select it in the Session Properties dialog -> Authentication panel.
"""
import java.lang.String, jarray
import org.parosproxy.paros.network.HttpRequestHeader as HttpRequestHeader
import org.parosproxy.paros.network.HttpHeader as HttpHeader
from org.apache.commons.httpclient import URI
from urllib import quote



LOGIN_BODY_FMTSTR = "password={password}"
LOGIN_URL = "https://127.0.0.1:8081/login"

SOURCE_PASSWD = ""


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
    requestBody = LOGIN_BODY_FMTSTR.format(password=SOURCE_PASSWD)
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
	