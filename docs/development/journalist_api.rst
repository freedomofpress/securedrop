Journalist Interface API
========================

This document describes the endpoints for SecureDrop's Journalist Interface
API.

Versioning
~~~~~~~~~~

The API is versioned and we are currently using version 1. This is set via the
base URL, which is:

.. code:: sh

  /api/v1/

Content Type
~~~~~~~~~~~~

Clients shall send the following headers:

.. code:: sh

  'Accept': 'application/json',
  'Content-Type': 'application/json'

Authentication
~~~~~~~~~~~~~~

``POST /api/v1/token`` to get a token with the username, password, and 2FA
token in the request body:

.. code:: sh

  {
  	"username": "journalist",
  	"password": "mypasswordgoeshere",
  	"one_time_code": "123456"
  }

Thereafter in order to authenticate to protected endpoints, send the token in
HTTP Authorization header:

.. code:: sh

  Authorization: Token yourtokengoeshere

This header will be checked with each API request to see if it is valid and
not yet expired. Tokens expire after 7200 seconds (120 minutes).

Endpoints
~~~~~~~~~

Root Endpoint
-------------

Does not require authentication.

The root endpoint describes the available resources:

.. code:: sh

  GET /api/v1/

Response 200 (application/json):

.. code:: sh

  {
    "current_user_url": "/api/v1/user/",
    "sources_url": "/api/v1/sources/",
    "submissions_url": "/api/v1/submissions/"
    "token_url": "/api/v1/token/"
  }

Sources ``[/sources]``
----------------------

Get all sources [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication. Provides a list of all sources and data about them
(such as number of documents, submissions, and their public key that replies
should be encrypted to).

.. code:: sh

  GET /api/v1/sources

Response 200 (application/json):

.. code:: sh

  {
      "sources": [
          {
              "add_star_url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/add_star/",
              "filesystem_id": "44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A=",
              "flagged": false,
              "interaction_count": 2,
              "journalist_designation": "olfactory yuppie",
              "last_updated": "Fri, 29 Jun 2018 19:11:28 GMT",
              "number_of_documents": 0,
              "number_of_messages": 2,
              "public_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFs2hGEBEACX9PSn9146bqup7MD3z4JLC2+m5GtXjOPmHVk7YRPwym7Q1XDx\n1exvXA1b17X6kj7TDPvBv8Gupro9BNAilPja+zB+m2JWKrdTjZYIWzZJ31WIC3Xm\nMs3V2dOZ1fCJlD+r2SiKLVzyODDpAoL42taxHXskhKgZvvUPsZv3abQctUOPtsWG\nKs9acPGGb/NnBVgPpdNzF7bKPpqqIHjMhb3WTEzGl8SYU/mfHx1DELzWmocB4v6s\nV4xMNKopyT44Or/ZeIGJf3SiTTsMSuU8IKfvzQKuCNT9IjWJmnYnYU+Zn/Zx/+q3\n1RWUs5z39e6OTT5qQwpxaharnJyM1u7vWY3R0rcZYkrAWQYgx/Ilf4/W1XSU7qmx\niH43mOupI1vQo0caJZwUvK83es2wmQsTNGJ1wqIU4pQU8nQzrlOuAWT3d/AjTXWh\nfFHMeRwfb2b2kRxp+hgFlC1hwpJG6o1+1kVUFUrh7N7Ln7WZi+UgQ23KGN1bU22D\nmY6fdEnssrODM8ly7AIHYhNOxtw/MnnWNlzt6n7gT26hN9VivXIczVxdkpV/vQz5\nng+olaLfXbf/yF/eTCmlsVdvALpDYYfO2VORcXe3JMTgXFzwQExz4auGdQlzH3ju\nmutOD5d0ETsgYP6lkO9wQrOqoqG/YnX+mUUc2H2wowYi5iFi11sLdbE7LQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8NDRZR1oyUjc2NDNUWEJBNjVaS1JPNUQ2UUgy\nNlJKN05WREZNUUpWRlNNTTZXQTVXM1pEWE5VWUtHQlRFVVlHRkNBQkJVRURMUTdP\nS1M2NTdXS09HVUhGTFZETFE3NUdXVE9YNEQ0QT0+iQI/BBMBCgApBQJbNoRhAhsv\nBQkB4M5fBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQvPRLirPeGcnf/w//\nXOvsO/N6UtQasiE121xa0AwKtptaRUoprEUP8af3+tQ28Ibo+Io1LLEQDODS4Btu\n7rz2eXjhw6XjvtGYXjbOVtXVHqynPZu2eW+er5cbi+zlSjnN7RyLndsg5PZ457q0\n5b1p4olGEPVTFhjKmFoWcYGmfW2q/QvqD9uz4BQWpevMwpop0k7dWf6FI8h3LQk9\n6RWDP1lqgNFSvIQNZnsOv/uluuH+txMcvDGT2aDzpiPTkuXlmHQXo3GEjOq+bVcU\npbhREB+syJi9klM/ZqOixbDKGSOdZQjBg3n6Tc09K26Cczk/sAs85039L5QSZiEL\niERfSiMWhv3X18sh7z4NLuHV4U1V0sIRzBuyzNJB2bGo4OEudsQtgjceno84n8gz\nQojBqdrvlz1dzRsCQb8pHmc94UDyFKLU0oZAwoG9kkUWu60fmveLr56h7pojrw/9\nQeMdKg6nM6bSAQoI29zSEAuSzUUa6DpIlF0dDrlP/+NZVfOI7Fq2JVKPSmKnclpE\n1DsYw9ZrRJhYnm1O9wuO7unXPQtaWLql401VbUG9EXKoghnHtjPVzPyFgCPs2lPZ\n3uei1TPU0fkedvv+4m5cMg5+a0N1kZmuIABidFVWqdpTSaXY5U24BOuW1W5bYcgF\npx0IUtZOiYrKhbVZ+FA6Y2codyHnCSYqZ91cp2uvqj4=\n=K/aW\n-----END PGP PUBLIC KEY BLOCK-----\n",
              "remove_star_url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/remove_star/",
              "reply_url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/reply/",
              "source_id": 1,
              "submissions_url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/submissions/",
              "url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/"
          },
          {
              "add_star_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/add_star/",
              "filesystem_id": "LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI=",
              "flagged": false,
              "interaction_count": 2,
              "journalist_designation": "clairvoyant burdock",
              "last_updated": "Fri, 29 Jun 2018 19:11:30 GMT",
              "number_of_documents": 0,
              "number_of_messages": 2,
              "public_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFs2hGQBEACnIkg5HQpABY/Rpmf8GhN96xqrEBABtK60FgomzdydGUlCip29\nPLzlMVFaAuGNJyo2S2izJr8n8TXmQYAQMP+OGdc+33In047NSCgF3ZGblUkexYKy\n/q8/Jr8YdLDeonJpYG0uQLnA2AA8FJucadkZCc30MPh+g7iPoKsmoRmr32GEpttS\n0XIfzjBhrc3uX1pEH8g9NP1CCHjbkLV1uY/Zo7svwPfbeEicXuK2TEl7ovlx8WYt\nz52sBwfsory2Eyy9D21IUKVBU1tWWeQeTAJrovg+auBZTwSV2+sYM7nE1zjWDDtA\nUSabvtP6O8dDO+vAMxmO80JxYONGfrS0XO5FSATpiApwsxS7o9ZSri3N+vLDQez4\npEQ0dkGa1NgTaUSVDzh+XIFWugd00wWg/rC6d3pZSjZXOA+p7BVUMsAfCLUZMxgz\n7JiqgZhM6TQ/RfReeSYDeUVT5ioImfDsOB79GArt+uvbesLxwLzoAcL6RWtqdK6k\nEcy277g7V5zsASJE6FAaYxS9dkqg9Zc+oSzlNtF7G0Kg3HIjZDwLoG+NzI7f4cMv\nXVka+GSHlWsElgE1My2HryC/SzqeVBbpg0vM8QaIMxiDrnLtjrD28L9Hi/5ab7Rq\nRF43lWWXQeEbKQ6nxLhQrVsM3E1xYx+JJLTBEJbNUo+TwTN7vfhAOpNJ4wARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8TEJJQ0YyRFBHSTNBTUQ3NEhJWVhRN1FLUUIz\nTUNDS05NUTZRNFZQT0wzT1lXTUlETVlETzZBMzdLT0pDWk5UM0dWT0VNQ0RIRUNN\nNFM0T0FYR0dNWjQ1MlNENDU0QTZFQURYTjNaST0+iQI/BBMBCgApBQJbNoRkAhsv\nBQkB4M5cBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQZmOkQ/49FwH1Yw/+\nIHhA2QpvDyThSwWthuh3ytdOJ9VveLO1jtBmDkuZtU/wpMgyVdCMusCOszXePSt5\n3neAcVOYFUBgKQTCmGAOXY8hOMNwHcdl13/ehiAwdj+BvE1OIBdLplCwW41F4esv\nvPvxBQW47oeRNt+u15keNXpWQBjFbB894yWQFlIn6sfEgvB9E53M2UHHn3NUzjKy\nIhC+ItMAodvEPpj34PAVPRxYk3TQkzsA/q9J48nAhY04x7lhSBp8M+jU07iGR2hB\nsewE/cwO5CVew7T7R5b1tl8iGIPmPeb4+zLc2xXy/oBAFRqI0BVdMskhtpmmvUzr\nScKN6GjX9a4TpOhxm3msyeKt5dnc3uOp3e7CBsDnYOTavDHeKvrkKZKukuvAXGt5\ne3RAITcvuOLVdswchwiex3HXq/rrvRHIglBaE56ZKo8XOm9+zBrcZzLjTmY1DChB\nhZGBX2p5tcZEN2h7n04BzFuPGNRB/PJa3A0qc3/aX3sJ8gGTovEt93Yzz6XyM70m\nBoo04NPwFv6JhEIm/qsbGTSFJO5NPONpaZ/54AKMldbIaq56eXz2si3Ltrl1pPIv\nqdmuW0VxMMt0l3xPZe3sBzNfp6MnWGjVYHfTIsXHbHgZWJKiMrhW9o2UjsmNlXUJ\n0asrUWe/LIDPk/5mB42CX1O6lwEkuo7uGoCa2F+8efs=\n=RC5t\n-----END PGP PUBLIC KEY BLOCK-----\n",
              "remove_star_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/remove_star/",
              "reply_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/reply/",
              "source_id": 2,
              "submissions_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/submissions/",
              "url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/"
          }
      ]
  }

Individual Source ``[/sources/<filesystem_id>]``
------------------------------------------------

Requires authentication

An object representing a single source.

Response 200 (application/json):

.. code:: sh

  {
      "add_star_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/add_star/",
      "filesystem_id": "LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI=",
      "flagged": false,
      "interaction_count": 2,
      "journalist_designation": "clairvoyant burdock",
      "last_updated": "Fri, 29 Jun 2018 19:11:30 GMT",
      "number_of_documents": 0,
      "number_of_messages": 2,
      "public_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFs2hGQBEACnIkg5HQpABY/Rpmf8GhN96xqrEBABtK60FgomzdydGUlCip29\nPLzlMVFaAuGNJyo2S2izJr8n8TXmQYAQMP+OGdc+33In047NSCgF3ZGblUkexYKy\n/q8/Jr8YdLDeonJpYG0uQLnA2AA8FJucadkZCc30MPh+g7iPoKsmoRmr32GEpttS\n0XIfzjBhrc3uX1pEH8g9NP1CCHjbkLV1uY/Zo7svwPfbeEicXuK2TEl7ovlx8WYt\nz52sBwfsory2Eyy9D21IUKVBU1tWWeQeTAJrovg+auBZTwSV2+sYM7nE1zjWDDtA\nUSabvtP6O8dDO+vAMxmO80JxYONGfrS0XO5FSATpiApwsxS7o9ZSri3N+vLDQez4\npEQ0dkGa1NgTaUSVDzh+XIFWugd00wWg/rC6d3pZSjZXOA+p7BVUMsAfCLUZMxgz\n7JiqgZhM6TQ/RfReeSYDeUVT5ioImfDsOB79GArt+uvbesLxwLzoAcL6RWtqdK6k\nEcy277g7V5zsASJE6FAaYxS9dkqg9Zc+oSzlNtF7G0Kg3HIjZDwLoG+NzI7f4cMv\nXVka+GSHlWsElgE1My2HryC/SzqeVBbpg0vM8QaIMxiDrnLtjrD28L9Hi/5ab7Rq\nRF43lWWXQeEbKQ6nxLhQrVsM3E1xYx+JJLTBEJbNUo+TwTN7vfhAOpNJ4wARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8TEJJQ0YyRFBHSTNBTUQ3NEhJWVhRN1FLUUIz\nTUNDS05NUTZRNFZQT0wzT1lXTUlETVlETzZBMzdLT0pDWk5UM0dWT0VNQ0RIRUNN\nNFM0T0FYR0dNWjQ1MlNENDU0QTZFQURYTjNaST0+iQI/BBMBCgApBQJbNoRkAhsv\nBQkB4M5cBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQZmOkQ/49FwH1Yw/+\nIHhA2QpvDyThSwWthuh3ytdOJ9VveLO1jtBmDkuZtU/wpMgyVdCMusCOszXePSt5\n3neAcVOYFUBgKQTCmGAOXY8hOMNwHcdl13/ehiAwdj+BvE1OIBdLplCwW41F4esv\nvPvxBQW47oeRNt+u15keNXpWQBjFbB894yWQFlIn6sfEgvB9E53M2UHHn3NUzjKy\nIhC+ItMAodvEPpj34PAVPRxYk3TQkzsA/q9J48nAhY04x7lhSBp8M+jU07iGR2hB\nsewE/cwO5CVew7T7R5b1tl8iGIPmPeb4+zLc2xXy/oBAFRqI0BVdMskhtpmmvUzr\nScKN6GjX9a4TpOhxm3msyeKt5dnc3uOp3e7CBsDnYOTavDHeKvrkKZKukuvAXGt5\ne3RAITcvuOLVdswchwiex3HXq/rrvRHIglBaE56ZKo8XOm9+zBrcZzLjTmY1DChB\nhZGBX2p5tcZEN2h7n04BzFuPGNRB/PJa3A0qc3/aX3sJ8gGTovEt93Yzz6XyM70m\nBoo04NPwFv6JhEIm/qsbGTSFJO5NPONpaZ/54AKMldbIaq56eXz2si3Ltrl1pPIv\nqdmuW0VxMMt0l3xPZe3sBzNfp6MnWGjVYHfTIsXHbHgZWJKiMrhW9o2UjsmNlXUJ\n0asrUWe/LIDPk/5mB42CX1O6lwEkuo7uGoCa2F+8efs=\n=RC5t\n-----END PGP PUBLIC KEY BLOCK-----\n",
      "remove_star_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/remove_star/",
      "reply_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/reply/",
      "source_id": 2,
      "submissions_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/submissions/",
      "url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/"
  }

Get all submissions associated with a source [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<filesystem_id>/submissions

Response 200 (application/json):

.. code:: sh

  {
      "submissions": [
          {
              "download_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/submissions/3/download/",
              "filename": "1-clairvoyant_burdock-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/",
              "submission_id": 3,
              "submission_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/submissions/3/"
          },
          {
              "download_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/submissions/4/download/",
              "filename": "2-clairvoyant_burdock-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/",
              "submission_id": 4,
              "submission_url": "/api/v1/sources/LBICF2DPGI3AMD74HIYXQ7QKQB3MCCKNMQ6Q4VPOL3OYWMIDMYDO6A37KOJCZNT3GVOEMCDHECM4S4OAXGGMZ452SD454A6EADXN3ZI%3D/submissions/4/"
          }
      ]
  }

Get a single submission associated with a source [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<filesystem_id>/submissions/<int:submission_id>

Response 200 (application/json):

.. code:: sh

  {
      "download_url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/submissions/1/download/",
      "filename": "1-olfactory_yuppie-msg.gpg",
      "is_read": false,
      "size": 604,
      "source_url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/",
      "submission_id": 1,
      "submission_url": "/api/v1/sources/44YGZ2R7643TXBA65ZKRO5D6QH26RJ7NVDFMQJVFSMM6WA5W3ZDXNUYKGBTEUYGFCABBUEDLQ7OKS657WKOGUHFLVDLQ75GWTOX4D4A%3D/submissions/1/"
  }

Add a reply to a source [``POST``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication. Clients are expected to encrypt replies prior to
submission to the server. Replies should be encrypted to the public key of the
source.

.. code:: sh

  POST /api/v1/sources/<filesystem_id>/reply

with the reply in the request body:

.. code:: sh

  {
   "reply": "-----BEGIN PGP MESSAGE-----[...]-----END PGP MESSAGE-----"
  }

Response 201 created (application/json):

.. code:: sh

  {
    "message": "Your reply has been stored"
  }

Replies that do not contain a GPG encrypted message will be rejected:

Response 400 (application/json):

.. code:: sh

  {
      "message": "You must encrypt replies client side"
  }

Delete a submission [``DELETE``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  DELETE /api/v1/sources/<filesystem_id>/submissions/<int:submission_id>

Response 200:

.. code:: sh

  {
    "message": "Submission deleted"
  }

Download a submission [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<filesystem_id>/submissions/<int:submission_id>/download

Response 200 will have ``Content-Type: application/pgp-encrypted`` and is the
content of the PGP encrypted submission.

Delete a Source and all their associated submissions [``DELETE``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  DELETE /api/v1/sources/<filesystem_id>/submissions

Response 200:

.. code:: sh

  {
    "message": "Source and submissions deleted"
  }

Star a source [``POST``]
^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  POST /api/v1/sources/<filesystem_id>/star

Response 201 created:

.. code:: sh

  {
    "message": "Star added"
  }

Remove a source [``DELETE``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  DELETE /api/v1/sources/<filesystem_id>/star

Response 200:

.. code:: sh

  {
    "message": "Star removed"
  }

Submission ``[/submissions]``
-----------------------------

Get all submissions [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication. This gets details of all submissions across sources.

.. code:: sh

  GET /api/v1/submissions

Response 200:

.. code:: sh

  {
      "submissions": [
          {
              "download_url": "/api/v1/sources/HUIQTCLJSN7PACRN4YTC4GUTGD2ZESBTTGAJ5LLFWL4UZY3RP4YE6NO2FL4NZLNFCAJE5TIJS7H3U5YTMC3Z3UNJNCB6PDHU5AMQBRA%3D/submissions/1/download/",
              "filename": "1-inspirational_busman-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/HUIQTCLJSN7PACRN4YTC4GUTGD2ZESBTTGAJ5LLFWL4UZY3RP4YE6NO2FL4NZLNFCAJE5TIJS7H3U5YTMC3Z3UNJNCB6PDHU5AMQBRA%3D/",
              "submission_id": 1,
              "submission_url": "/api/v1/sources/HUIQTCLJSN7PACRN4YTC4GUTGD2ZESBTTGAJ5LLFWL4UZY3RP4YE6NO2FL4NZLNFCAJE5TIJS7H3U5YTMC3Z3UNJNCB6PDHU5AMQBRA%3D/submissions/1/"
          },
          {
              "download_url": "/api/v1/sources/HUIQTCLJSN7PACRN4YTC4GUTGD2ZESBTTGAJ5LLFWL4UZY3RP4YE6NO2FL4NZLNFCAJE5TIJS7H3U5YTMC3Z3UNJNCB6PDHU5AMQBRA%3D/submissions/2/download/",
              "filename": "2-inspirational_busman-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/HUIQTCLJSN7PACRN4YTC4GUTGD2ZESBTTGAJ5LLFWL4UZY3RP4YE6NO2FL4NZLNFCAJE5TIJS7H3U5YTMC3Z3UNJNCB6PDHU5AMQBRA%3D/",
              "submission_id": 2,
              "submission_url": "/api/v1/sources/HUIQTCLJSN7PACRN4YTC4GUTGD2ZESBTTGAJ5LLFWL4UZY3RP4YE6NO2FL4NZLNFCAJE5TIJS7H3U5YTMC3Z3UNJNCB6PDHU5AMQBRA%3D/submissions/2/"
          },
          {
              "download_url": "/api/v1/sources/C7YGA52VCSAILDUGWQININHKV7MO3SPUV67HAZKDGKDEVMBZPNGAJSGN7JTG5CZ7WNA4VR36ZKQ7BPI4Z544WBBBOTLRTAYO7LAVPUA%3D/submissions/3/download/",
              "filename": "1-masculine_internationalization-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/C7YGA52VCSAILDUGWQININHKV7MO3SPUV67HAZKDGKDEVMBZPNGAJSGN7JTG5CZ7WNA4VR36ZKQ7BPI4Z544WBBBOTLRTAYO7LAVPUA%3D/",
              "submission_id": 3,
              "submission_url": "/api/v1/sources/C7YGA52VCSAILDUGWQININHKV7MO3SPUV67HAZKDGKDEVMBZPNGAJSGN7JTG5CZ7WNA4VR36ZKQ7BPI4Z544WBBBOTLRTAYO7LAVPUA%3D/submissions/3/"
          },
          {
              "download_url": "/api/v1/sources/C7YGA52VCSAILDUGWQININHKV7MO3SPUV67HAZKDGKDEVMBZPNGAJSGN7JTG5CZ7WNA4VR36ZKQ7BPI4Z544WBBBOTLRTAYO7LAVPUA%3D/submissions/4/download/",
              "filename": "2-masculine_internationalization-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/C7YGA52VCSAILDUGWQININHKV7MO3SPUV67HAZKDGKDEVMBZPNGAJSGN7JTG5CZ7WNA4VR36ZKQ7BPI4Z544WBBBOTLRTAYO7LAVPUA%3D/",
              "submission_id": 4,
              "submission_url": "/api/v1/sources/C7YGA52VCSAILDUGWQININHKV7MO3SPUV67HAZKDGKDEVMBZPNGAJSGN7JTG5CZ7WNA4VR36ZKQ7BPI4Z544WBBBOTLRTAYO7LAVPUA%3D/submissions/4/"
          }
      ]
  }

User ``[/user]``
----------------

Get an object representing the current user [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/user

Response 200:

.. code:: sh

  {
      "is_admin": true,
      "last_login": "Fri, 29 Jun 2018 20:13:53 GMT",
      "username": "journalist"
  }
