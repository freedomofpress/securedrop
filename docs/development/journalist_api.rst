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
  	"passphrase": "monkey potato pizza quality silica growing deduce",
  	"one_time_code": "123456"
  }

This will produce a response with your Authorization token:

.. code:: sh

  {
      "expiration": "2018-07-10T04:29:41.696321Z",
      "token": "eyJhbGciOiJIUzI1NiIsImV4cCI6MTUzMTE5Njk4MSwiaWF0IjoxNTMxMTY4MTgxfQ.eyJpZCI6MX0.TBSvfrICMxtvWgpVZzqTl6wHYNQuGPOaZpuAKwwIXXo",
      "journalist_uuid": "54d81dae-9d94-4145-8a57-4c804a04cfe0"
  }

Thereafter in order to authenticate to protected endpoints, send the token in
HTTP Authorization header:

.. code:: sh

  Authorization: Token eyJhbGciOiJIUzI1NiIsImV4cCI6MTUzMDU4NjU4MiwifWF0IjoxNTMwNTc5MzgyfQ.eyJpZCI6MX0.P_PfcLMk1Dq5VCIANo-lJbu0ZyCL2VcT8qf9fIZsTCM

This header will be checked with each API request to see if it is valid and
not yet expired. Tokens currently expire after 8 hours, but note that clients
should use the expiration time provided in the response to determine when
the token will expire. After the token expires point, users must
login again. Clients implementing logout functionality should delete tokens
locally upon logout.

Errors
~~~~~~

The API will respond to all errors (400-599) with a JSON object with the
following fields:

.. code:: sh

  {
    "message": "This is a detailed error message."
  }

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
    "current_user_url": "/api/v1/user",
    "sources_url": "/api/v1/sources",
    "submissions_url": "/api/v1/submissions",
    "replies_url": "/api/v1/replies",
    "token_url": "/api/v1/token"
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
              "add_star_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/add_star",
              "interaction_count": 2,
              "is_flagged": false,
              "is_starred": false,
              "journalist_designation": "validated benefactress",
              "key": {
                  "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtEA0YBEAChcaDWfnLvMNDypxF+YhNI/P0wYw7+kGGTCAr+pChzV1I3ZEBO\nOz3NU4G5+MYHstD3m4Cdcwdvo+S6E66B4h/9xWWtJLzBMmRNBrCpfny8id1QyNsd\n2PPYk2Dt6Xs9RZaHO3sd8nXVx07FwYmMzNa3UlRg6kb0EUwzNDOW0jaramutp1c0\noTHiEiHJ9wQLNnU55kIXBg6XTNpquCj8O6Vpnsgr0HCC+Fr9hno8u58seYUnyhaN\n3PNE7d96H3O1MNGk0L10vt1u/449DoYFeWR1GnhssfAlVjhizf1sflNXCybjACqK\ngVMsKnYpDWzIXOPF7jNW7jn/N3EpGhq1pjjAJ4LNPXnsTgCmkA5okcPSPIhUH2gN\n6WVtPryGQ9iV5cWgL2KDq35VoZ+6+raANAeE23yAnJW9c7HLRckeB429GNAu1TKR\nkNmDe6zmuhwM2VA+JDN23gFjl7uMgN9bVz6pAyA+0eUQG6Ak3fJmCAGdNIx0/Htq\nRgUwElpHDbrp8kzmadfdWVwq/Tf373FE5TFL2mQ7EVI8xQ4HWvhWRFjpQKWRzBsg\nBLXWzr2C6coQywNLUvJ0JEkm/Uihd5341JoRuotUAY8pwA3CWUTSSi/7yBBAJzRk\nNy7XivylH084DM2/EJaq5gNbHJ7jA31YymwQdw3OmIqX4K07zS2AdGX20QARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8TTdOUEo3RVJNQU9KREhPSUpaUTIzVEdTTlFR\nR0JIQTNEVUJMUjdFUDQ1R0pKWVJGVkpSTFVSSDI0NjRBS1dMTjYyVFNSWFNJMzJE\nNkQzTjdXVTRFWTU3SzdBRkpZVFpHR0NUQkFKUT0+iQI/BBMBCgApBQJbRANGAhsv\nBQkB4c/6BwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQDDX++nndxld+CA/9\nGoG3Xm3e2pyW+itxKC/gOJiK/PXk/nrpNXF5d1b1TEbkMMmMy2Dw4YC/7btr3Q0D\nEUg5qXiIO+Tw9KNS1udTVJggG+jWehlgOMb0+Z7JUawPCwAFjU17BRdRVDv39Y5G\nGJSM68/e8n5HXLNx1ABFlm0qfGQQw+/anwwxCnJb5KgSZ64mZiYtjVNiaqrtxxB7\nXu6AOsTlWgzT5rkwrq6gZsdG53gRYQiaVLS8BDKT4WD45iYKR5nn0BvPN6/L+4UG\nQj0l2lbAuQGMuMVKCeRYIJEDzTeqHzxuqkrr79pBZz1rNSNWYmaYo5V7ZH1VIl5y\n+jf1mEbvhNQUoy2HCoTUGPJjpgg7LyN7S6eZH/J5Q8gHD4s+rnQbzJHwD3u5y3L+\nDtz3trQs6K6CcqsyYBCS0oH3DSYO9SJiBJqgoSKKs8/YtqWupDXUFCjcYgdxDEmR\nLw+Ovd0wEbs7JoMcpRtx3LHgpL6ICFZqFvA3IyTo6OCa8ZCCnvtkLvlinUg0TGTc\nmvThHu/1jbDZjAPWRiuoEcHz5XyFSrCzkXKvXEDqlsK1WADNWZlznfBhu9EgciHP\nlOAJrKulOC4TaRmHP+K5MFowmwB1IY9yErhvAobTnZn7sXqc2AY5cTPfphvuHJwR\nFwtb1yZ6TEBSiLywZguTHurVeIyKW4C2jSlqyV1BnH8=\n=/Wxo\n-----END PGP PUBLIC KEY BLOCK-----\n",
                  "type": "PGP"
              },
              "last_updated": "2018-07-10T00:52:21.157409Z",
              "number_of_documents": 0,
              "number_of_messages": 2,
              "remove_star_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/remove_star",
              "replies_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/replies",
              "submissions_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/submissions",
              "url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a",
              "uuid": "9b6df7c9-a6b1-461d-91f0-5b715fc7a47a"
          },
          {
              "add_star_url": "/api/v1/sources/f086bd03-1c89-49fb-82d5-00084c17b4ce/add_star",
              "interaction_count": 2,
              "is_flagged": false,
              "is_starred": false,
              "journalist_designation": "navigational firearm",
              "key": {
                  "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtEA0sBEACsJK+UPZoemYts+L+4JnhsRXJqixMO2BDJEueiGg2Aq0CEI4pz\nmNq5Xn/ZjHChnh/3AEc/Svv1IpA8RH4cgTfKTzpv5OnEwk6+0FUgr2rhCLzju9At\nrdhE1wFhldSWU4RyB/sC0L20HSP0H6Uj2xsT+gqw06fNvEzHKEpGt9dR6hQxH9Hf\new0z/p8Oov7x5wRRnZbe1VezlAM4L7BsboBUNrLsnKi7BvZFihRrL+CYaSH/XZ1E\n/6aBNPol9zVEeG8A+L21TVvBsjHb76Jr5t9iIl1kd1z3mMgq9cZacal96aONISLU\nv3pdlpY+5lBFLvhiSfFcNNNwMkglKmzRxNVcmxhUMquFpUHlsLxcz177cftkR0qD\nJhyVqeYEWeZgJ8IRFWaRK5NvCCLSJoLtAYcx7IRRBZJ7Y5rGBPH6rjYw75fXhDHq\n+ApL5/iVPkxrKdYfBxQApuYNW0pUpML9GSGpBiF8ri3C11dKIfMjwO6a69YNoJi2\nqiu/7p+BIHLCrdHlYZCHTgrYXlx0uNR9pVry7ioNNekJaoBcXIfsL5n5QiVS9rX+\nNSNsUF+yEB/9OFFywwaHlvMLYBMm1ikiU7DAbxowJxbw7Sh8N/sP1LMiv/2YUHiT\nqUJHBdyuOvaVFhcgrXUKPaX2B/yaTjXl/9u0sSfM9uoGyRQoj+OwtwC7BwARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8SFNNM1FVNTdUQUdHVjNEVkU0UUFFRkxUVkU1\nNEk2T1ZSU0lSSkJOWE5CVTZYWUlYNDRFVzZJNFdHSkY0U1dVS1hKQlhFSTZKQ0NW\nNkREM0ZGM1BZQ1hXM1NYTlJORk5DSERGWVBFST0+iQI/BBMBCgApBQJbRANLAhsv\nBQkB4c/1BwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQ3ZWCdf0oVBq5EQ/9\nEUvasqWfeyidKAcHfXa/mu0ENyeDbDXgJNiZB867v3MaZWUn+5qy+SRcDGev1TBl\nwOzSt7uao6Zrqi9/Lexe07xjLEGRGYolZwOFLP+vlULpsgncen8lpENwrtY9MO3w\nbiobArNhp0kCvn6aiUi8Lb3nl57FpJ9dKfhMmP7evf0DcEvFcsDBoR7LHkMgEHQX\n5WbkvMyO7eoU+S4KrtU8PbR03j3cDv+YvLCJnwJyO79SqbkxafmAKD5KaUnsRTK5\nvoIeDH5dhGOQI0/YpCcCNZJP187rooOwlBL+R2r+LhyjK5YUEH1XKz9z8M6oQirZ\ntG8JbZbxCc19OnhL3SijsGVpqIuENd0VuNA1TLfzlbhJ/AYMBcQgRSU3a0kWRA3+\nNEZ5vEQkWtaL2bxDv2TkJdbS335nCBkuOIJgVMGiy9OjZdT58zEqpMupBWCzA67O\nLdovCyvNErWcs30QUqVRHreIaUMEQBcqtWJAhnfdfXNaQUr3ac0oopEZi30I9uDW\nejVc+ml00nTeg3WLqibjaJkid8QTfwkxx4oJ4WJaCgq/b0UvyBxD04N/ZpJHG2ja\n28uQ8v9rBJgTPR5uZNw4of842u17J6F65x7+phnoy6ayXCV0fwgzjSg85dPUUPIT\ns1CnQxnBjVUbCHELdx2LR7XSmVwkAHBVJ1NALCMiQic=\n=pmcO\n-----END PGP PUBLIC KEY BLOCK-----\n",
                  "type": "PGP"
              },
              "last_updated": "2018-07-10T00:52:25.696391Z",
              "number_of_documents": 0,
              "number_of_messages": 2,
              "remove_star_url": "/api/v1/sources/f086bd03-1c89-49fb-82d5-00084c17b4ce/remove_star",
              "replies_url": "/api/v1/sources/f086bd03-1c89-49fb-82d5-00084c17b4ce/replies",
              "submissions_url": "/api/v1/sources/f086bd03-1c89-49fb-82d5-00084c17b4ce/submissions",
              "url": "/api/v1/sources/f086bd03-1c89-49fb-82d5-00084c17b4ce",
              "uuid": "f086bd03-1c89-49fb-82d5-00084c17b4ce"
          }
      ]
  }

Individual Source ``[/sources/<source_uuid>]``
----------------------------------------------

Requires authentication

An object representing a single source.

Response 200 (application/json):

.. code:: sh

  {
      "add_star_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/add_star",
      "interaction_count": 2,
      "is_flagged": false,
      "is_starred": false,
      "journalist_designation": "validated benefactress",
      "key": {
          "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtEA0YBEAChcaDWfnLvMNDypxF+YhNI/P0wYw7+kGGTCAr+pChzV1I3ZEBO\nOz3NU4G5+MYHstD3m4Cdcwdvo+S6E66B4h/9xWWtJLzBMmRNBrCpfny8id1QyNsd\n2PPYk2Dt6Xs9RZaHO3sd8nXVx07FwYmMzNa3UlRg6kb0EUwzNDOW0jaramutp1c0\noTHiEiHJ9wQLNnU55kIXBg6XTNpquCj8O6Vpnsgr0HCC+Fr9hno8u58seYUnyhaN\n3PNE7d96H3O1MNGk0L10vt1u/449DoYFeWR1GnhssfAlVjhizf1sflNXCybjACqK\ngVMsKnYpDWzIXOPF7jNW7jn/N3EpGhq1pjjAJ4LNPXnsTgCmkA5okcPSPIhUH2gN\n6WVtPryGQ9iV5cWgL2KDq35VoZ+6+raANAeE23yAnJW9c7HLRckeB429GNAu1TKR\nkNmDe6zmuhwM2VA+JDN23gFjl7uMgN9bVz6pAyA+0eUQG6Ak3fJmCAGdNIx0/Htq\nRgUwElpHDbrp8kzmadfdWVwq/Tf373FE5TFL2mQ7EVI8xQ4HWvhWRFjpQKWRzBsg\nBLXWzr2C6coQywNLUvJ0JEkm/Uihd5341JoRuotUAY8pwA3CWUTSSi/7yBBAJzRk\nNy7XivylH084DM2/EJaq5gNbHJ7jA31YymwQdw3OmIqX4K07zS2AdGX20QARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8TTdOUEo3RVJNQU9KREhPSUpaUTIzVEdTTlFR\nR0JIQTNEVUJMUjdFUDQ1R0pKWVJGVkpSTFVSSDI0NjRBS1dMTjYyVFNSWFNJMzJE\nNkQzTjdXVTRFWTU3SzdBRkpZVFpHR0NUQkFKUT0+iQI/BBMBCgApBQJbRANGAhsv\nBQkB4c/6BwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQDDX++nndxld+CA/9\nGoG3Xm3e2pyW+itxKC/gOJiK/PXk/nrpNXF5d1b1TEbkMMmMy2Dw4YC/7btr3Q0D\nEUg5qXiIO+Tw9KNS1udTVJggG+jWehlgOMb0+Z7JUawPCwAFjU17BRdRVDv39Y5G\nGJSM68/e8n5HXLNx1ABFlm0qfGQQw+/anwwxCnJb5KgSZ64mZiYtjVNiaqrtxxB7\nXu6AOsTlWgzT5rkwrq6gZsdG53gRYQiaVLS8BDKT4WD45iYKR5nn0BvPN6/L+4UG\nQj0l2lbAuQGMuMVKCeRYIJEDzTeqHzxuqkrr79pBZz1rNSNWYmaYo5V7ZH1VIl5y\n+jf1mEbvhNQUoy2HCoTUGPJjpgg7LyN7S6eZH/J5Q8gHD4s+rnQbzJHwD3u5y3L+\nDtz3trQs6K6CcqsyYBCS0oH3DSYO9SJiBJqgoSKKs8/YtqWupDXUFCjcYgdxDEmR\nLw+Ovd0wEbs7JoMcpRtx3LHgpL6ICFZqFvA3IyTo6OCa8ZCCnvtkLvlinUg0TGTc\nmvThHu/1jbDZjAPWRiuoEcHz5XyFSrCzkXKvXEDqlsK1WADNWZlznfBhu9EgciHP\nlOAJrKulOC4TaRmHP+K5MFowmwB1IY9yErhvAobTnZn7sXqc2AY5cTPfphvuHJwR\nFwtb1yZ6TEBSiLywZguTHurVeIyKW4C2jSlqyV1BnH8=\n=/Wxo\n-----END PGP PUBLIC KEY BLOCK-----\n",
          "type": "PGP"
      },
      "last_updated": "2018-07-10T00:52:21.157409Z",
      "number_of_documents": 0,
      "number_of_messages": 2,
      "remove_star_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/remove_star",
      "replies_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/replies",
      "submissions_url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a/submissions",
      "url": "/api/v1/sources/9b6df7c9-a6b1-461d-91f0-5b715fc7a47a",
      "uuid": "9b6df7c9-a6b1-461d-91f0-5b715fc7a47a"
  }

Get all submissions associated with a source [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<source_uuid>/submissions

Response 200 (application/json):

.. code:: sh

  {
      "submissions": [
          {
              "download_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/4c2e701c-70d2-4cb5-87c0-de59c2ebbc62/download",
              "filename": "1-dejected_respondent-msg.gpg",
              "is_read": false,
              "size": 603,
              "source_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241",
              "submission_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/4c2e701c-70d2-4cb5-87c0-de59c2ebbc62",
              "uuid": "4c2e701c-70d2-4cb5-87c0-de59c2ebbc62"
          },
          {
              "download_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/c2e00865-8f75-444a-b5b4-88424024ce69/download",
              "filename": "2-dejected_respondent-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241",
              "submission_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/c2e00865-8f75-444a-b5b4-88424024ce69",
              "uuid": "c2e00865-8f75-444a-b5b4-88424024ce69"
          }
      ]
  }

Get a single submission associated with a source [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<source_uuid>/submissions/<submission_uuid>

Response 200 (application/json):

.. code:: sh

  {
      "download_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/4c2e701c-70d2-4cb5-87c0-de59c2ebbc62/download",
      "filename": "1-dejected_respondent-msg.gpg",
      "is_read": false,
      "size": 603,
      "source_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241",
      "submission_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/4c2e701c-70d2-4cb5-87c0-de59c2ebbc62",
      "uuid": "4c2e701c-70d2-4cb5-87c0-de59c2ebbc62"
  }

Get all replies associated with a source [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<source_uuid>/replies

Response 200 (application/json):

.. code:: sh

  {
      "replies": [
          {
              "filename": "3-famished_sheep-reply.gpg",
              "is_deleted_by_source": false,
              "journalist_username": "journalist",
              "journalist_uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738",
              "reply_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5/replies/98cc4ed6-6ac5-4867-b144-f97d0497f2c1",
              "size": 1116,
              "source_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5",
              "uuid": "98cc4ed6-6ac5-4867-b144-f97d0497f2c1"
          },
          {
              "filename": "4-famished_sheep-reply.gpg",
              "is_deleted_by_source": false,
              "journalist_username": "journalist",
              "journalist_uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738",
              "reply_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5/replies/2863e3ec-66c8-4b74-ba43-615c805be4da",
              "size": 1116,
              "source_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5",
              "uuid": "2863e3ec-66c8-4b74-ba43-615c805be4da"
          }
      ]
  }

Get a single reply associated with a source [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<source_uuid>/replies/<reply_uuid>

Response 200 (application/json):

.. code:: sh

  {
      "filename": "3-famished_sheep-reply.gpg",
      "is_deleted_by_source": false,
      "journalist_username": "journalist",
      "journalist_uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738",
      "reply_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5/replies/98cc4ed6-6ac5-4867-b144-f97d0497f2c1",
      "size": 1116,
      "source_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5",
      "uuid": "98cc4ed6-6ac5-4867-b144-f97d0497f2c1"
  }

Download a reply [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<source_uuid>/replies/<reply_uuid>/download

Response 200 will have ``Content-Type: application/pgp-encrypted`` and is the
content of the PGP encrypted reply.

An ETag header is also present containing the SHA256 hash of the response data:

.. code:: sh

  "sha256:c757c5aa263dc4a5a2bca8e7fe973367dbd2c1a6c780d19c0ba499e6b1b81efa"

Note that these are not intended for cryptographic purposes and are present
for clients to check that downloads are not corrupted.

Delete a reply [``DELETE``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  DELETE /api/v1/sources/<source_uuid>/replies/<reply_uuid>

Response 200:

.. code:: sh

  {
    "message": "Reply deleted"
  }

Add a reply to a source [``POST``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication. Clients are expected to encrypt replies prior to
submission to the server. Replies should be encrypted to the public key of the
source.

Including the ``uuid`` field in the request is optional. Clients may want to
pre-set the ``uuid`` so they can track in-flight messages.

.. code:: sh

  POST /api/v1/sources/<source_uuid>/replies

with the reply in the request body:

.. code:: json

  {
   "uuid": "0bc588dd-f613-4999-b21e-1cebbd9adc2c",
   "reply": "-----BEGIN PGP MESSAGE-----[...]-----END PGP MESSAGE-----"
  }

Response 201 created (application/json):

.. code:: json

  {
    "message": "Your reply has been stored",
    "uuid": "0bc588dd-f613-4999-b21e-1cebbd9adc2c"
  }

The returned ``uuid`` field is the UUID of the reply and can be used to
reference this reply later. If the client set the ``uuid`` in the request,
this will have the same value.

Replies that do not contain a GPG encrypted message will be rejected:

Response 400 (application/json):

.. code:: json

  {
      "message": "You must encrypt replies client side"
  }

Delete a submission [``DELETE``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  DELETE /api/v1/sources/<source_uuid>/submissions/<submission_uuid>

Response 200:

.. code:: sh

  {
    "message": "Submission deleted"
  }

Download a submission [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  GET /api/v1/sources/<source_uuid>/submissions/<submission_uuid>/download

Response 200 will have ``Content-Type: application/pgp-encrypted`` and is the
content of the PGP encrypted submission.

An ETag header is also present containing the SHA256 hash of the response data:

.. code:: sh

  "sha256:c757c5aa263dc4a5a2bca8e7fe973367dbd2c1a6c780d19c0ba499e6b1b81efa"

Note that these are not intended for cryptographic purposes and are present
for clients to check that downloads are not corrupted.

Delete a Source and all their associated submissions [``DELETE``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  DELETE /api/v1/sources/<source_uuid>

Response 200:

.. code:: sh

  {
    "message": "Source and submissions deleted"
  }

Star a source [``POST``]
^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  POST /api/v1/sources/<source_uuid>/star

Response 201 created:

.. code:: sh

  {
    "message": "Star added"
  }

Remove a source [``DELETE``]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  DELETE /api/v1/sources/<source_uuid>/star

Response 200:

.. code:: sh

  {
    "message": "Star removed"
  }

Flag a source [``POST``]
^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  POST /api/v1/sources/<source_uuid>/flag

Response 200:

.. code:: sh

  {
    "message": "Source flagged for reply"
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
              "download_url": "/api/v1/sources/1ed4c191-c6b1-463b-92a5-102deaf7d40a/submissions/e58f6206-fc12-4dbe-9a9c-84c3d82eea2f/download",
              "filename": "1-abridged_psalmist-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/1ed4c191-c6b1-463b-92a5-102deaf7d40a",
              "submission_url": "/api/v1/sources/1ed4c191-c6b1-463b-92a5-102deaf7d40a/submissions/e58f6206-fc12-4dbe-9a9c-84c3d82eea2f",
              "uuid": "e58f6206-fc12-4dbe-9a9c-84c3d82eea2f"
          },
          {
              "download_url": "/api/v1/sources/1ed4c191-c6b1-463b-92a5-102deaf7d40a/submissions/a93d4123-a984-4740-9849-772c30694bab/download",
              "filename": "2-abridged_psalmist-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/1ed4c191-c6b1-463b-92a5-102deaf7d40a",
              "submission_url": "/api/v1/sources/1ed4c191-c6b1-463b-92a5-102deaf7d40a/submissions/a93d4123-a984-4740-9849-772c30694bab",
              "uuid": "a93d4123-a984-4740-9849-772c30694bab"
          },
          {
              "download_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/4c2e701c-70d2-4cb5-87c0-de59c2ebbc62/download",
              "filename": "1-dejected_respondent-msg.gpg",
              "is_read": false,
              "size": 603,
              "source_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241",
              "submission_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/4c2e701c-70d2-4cb5-87c0-de59c2ebbc62",
              "uuid": "4c2e701c-70d2-4cb5-87c0-de59c2ebbc62"
          },
          {
              "download_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/c2e00865-8f75-444a-b5b4-88424024ce69/download",
              "filename": "2-dejected_respondent-msg.gpg",
              "is_read": false,
              "size": 604,
              "source_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241",
              "submission_url": "/api/v1/sources/598b859c-72c7-4e53-a68c-b725eb514241/submissions/c2e00865-8f75-444a-b5b4-88424024ce69",
              "uuid": "c2e00865-8f75-444a-b5b4-88424024ce69"
          }
      ]
  }

Reply ``[/replies]``
--------------------

Get all replies [``GET``]
^^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication. This gets details of all replies across sources.

.. code:: sh

  GET /api/v1/replies

Response 200:

.. code:: sh

  {
      "replies": [
          {
              "filename": "3-famished_sheep-reply.gpg",
              "is_deleted_by_source": false,
              "journalist_username": "journalist",
              "journalist_uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738",
              "reply_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5/replies/98cc4ed6-6ac5-4867-b144-f97d0497f2c1",
              "size": 1116,
              "source_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5",
              "uuid": "98cc4ed6-6ac5-4867-b144-f97d0497f2c1"
          },
          {
              "filename": "4-famished_sheep-reply.gpg",
              "is_deleted_by_source": false,
              "journalist_username": "journalist",
              "journalist_uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738",
              "reply_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5/replies/2863e3ec-66c8-4b74-ba43-615c805be4da",
              "size": 1116,
              "source_url": "/api/v1/sources/f381dbb4-4bb5-451a-801a-e961461af6e5",
              "uuid": "2863e3ec-66c8-4b74-ba43-615c805be4da"
          },
          {
              "filename": "3-intermittent_proline-reply.gpg",
              "is_deleted_by_source": false,
              "journalist_username": "journalist",
              "journalist_uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738",
              "reply_url": "/api/v1/sources/06bfd5ba-ed6a-4850-b713-4e6940b74931/replies/33b35f6e-b43e-4ad5-a24b-37fd1916ad75",
              "size": 1116,
              "source_url": "/api/v1/sources/06bfd5ba-ed6a-4850-b713-4e6940b74931",
              "uuid": "33b35f6e-b43e-4ad5-a24b-37fd1916ad75"
          },
          {
              "filename": "4-intermittent_proline-reply.gpg",
              "is_deleted_by_source": false,
              "journalist_username": "journalist",
              "journalist_uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738",
              "reply_url": "/api/v1/sources/06bfd5ba-ed6a-4850-b713-4e6940b74931/replies/6fad52dd-bc55-42aa-96da-4636644fb3e2",
              "size": 1116,
              "source_url": "/api/v1/sources/06bfd5ba-ed6a-4850-b713-4e6940b74931",
              "uuid": "6fad52dd-bc55-42aa-96da-4636644fb3e2"
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
    "last_login": "2018-07-09T20:29:41.696782Z",
    "username": "journalist",
    "uuid": "a2405127-1c9e-4a3a-80ea-95f6a71e5738"
  }
