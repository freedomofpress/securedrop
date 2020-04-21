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

``POST /api/v1/token`` to get a token with the username, password, and two-factor
code in the request body:

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
      "journalist_uuid": "54d81dae-9d94-4145-8a57-4c804a04cfe0",
      "journalist_first_name": "daniel",
      "journalist_last_name": "ellsberg"
  }

Thereafter in order to authenticate to protected endpoints, send the token in
HTTP Authorization header:

.. code:: sh

  Authorization: Token eyJhbGciOiJIUzI1NiIsImV4cCI6MTUzMDU4NjU4MiwifWF0IjoxNTMwNTc5MzgyfQ.eyJpZCI6MX0.P_PfcLMk1Dq5VCIANo-lJbu0ZyCL2VcT8qf9fIZsTCM

This header will be checked with each API request to see if it is valid and
not yet expired. Tokens currently expire after 8 hours.

Logout
------

Clients should use the logout endpoint to invalidate their token:

``POST /api/v1/logout`` with the token in the HTTP Authorization header
and you will get the following response upon successful invalidation of the
API token:

.. code:: sh

  {
  "message": "Your token has been revoked."
  }

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
                "fingerprint": "8C71EA66B0278309A31DBD691733DA655854DB12",
                "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFGRfoABEACf5Y+6prky4JcWmKSsuh/52ZLw1FTCqrgAIK0QVFZ+cy2riFHv\njQXYB4bPOCt7PmYbmMxxIWkXqJCaPVkLbpi7p5X2Wkgh+qGgjIjotq2Y9iPP6KQ3\nGvJdpG3rWwbOsrt4rDh/L/lStn+ty4io3cDr7l7ISOtOcmOPKeKv6eGxSmCAYsnJ\nKKsIWcSjfb82KhCzL/BBApqXt9uc6Jqjh1RPL3bGIG0tq37yX/zbFefDBDF8m8d6\nc7pvvYMaO90PGViBVg6hh8+rPq/rK7YyHOWZlt6MXw7cm/GaH+DkGxGKe8Yuj92R\nOPNQFfpAI/tXldEcEvdG/4mba7uxrEMe33tsnbQamFZtXFAIrSjXa9O4CEEWnRCz\nNE90u9FeM4bk/lModsr7gOrWbO6QwctVt/YnvI7blUXzpMzDsbgvR89auKS9VHGZ\nY5L3yz0yVwRAIw3/CwsJEYajKiPadcExhZhc8OCTTe8zPXxQ8OWrvmFBA6x6cfvq\nSqoH3NXrDVY/6w9dCqVXitcYynATqm0Qkkr81jXE3BEfx7AQPXHXGasvFM1mqeQU\n+WQPqUKheomy7/7z3heasKub3MYLkuW6y7c31z6cmvt6h5fYcNPvQXCox4BJkVcK\nPbzst612sbqhTQEeSsDnVU1sPLxpfbxFfKuWQlEV8kfm4JsMbryqG9Z0RQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8UFlNR0IzRE9BNVFLVFozNjVPUTNQWUpDMk9a\nQ0RXQjIyM1dFS1Q3V0o1NDI0QUZUT1ZFSjI0SEpaSFRYQTZTQjVGUkFBVjdHRVFQ\nS01HQjQzUUxMVzNTRUxFWENYWklVRk5QWTU2WT0+iQI3BBMBCgAhBQJRkX6AAhsv\nBQsJCAcCBhUICQoLAgQWAgMBAh4BAheAAAoJEBcz2mVYVNsSQ88P/3e54noTBb/O\nFVVNYw5oY9zIQPsoYUkCCvKCv26bi3qpfsDWjohyupKLth9AfFBTk3oiNhzeFhiv\nZ5RbLgJYAWuzWNdMCSd3RAqZbbzFx3255oR9t+/RNwjeOqKpoO313myAKsRR1z+N\nbRF0A1C8GiMOCrvV/9p+rsTDrv+8fXkrQz55nGkt6JlI43EqlH0Eg7wxI+HMgTdz\nsPWBR63INNhkrR5Ln7YShOBmnUWjpEjFYvZlAbzkMbbfznDZ2g7auRpT0S8vNgcG\n9k9dG3gpMFnHiaE4SmdOIb82qv9X6Q7Owwxmz85JAe/P/CYsndUbRHSfXMp16igm\nj0RfcC7J0E/SkwBY9jc+YtGCWfqqXa1a4uY03vN1YqqFWqb+exa/Qv14wwgcS17p\n8O/X1y9gPV0qleikFgNt8sPd+a2lVdRSjh4Xh7l6eTHMqoDUJXtFu0evSg3oBFZj\n8OIXe8KZltJCYlxN+1/xlvZjAVfmYT6kxOXYsPB3o3Z9Hemgsw2PnjI04ZMwTSyb\n101xfgB1XBd1Hrv9WQ5PNoPwXRhx7/bfzQWTx/uP8luT6yqEerLiF0m/ShvYvKQa\ncLuwtW3Rlj1BD5CpdG+491jJ6cRXq8xfYmCd2MmBTtMAoq4DobYw75NKIssZ5gs6\nu6NXuCWOsf8lQNBKxkNpuohLlTef8n1y\n=Zp4Z\n-----END PGP PUBLIC KEY BLOCK-----\n",
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
                "fingerprint": "C20D06197FFAE44552358AA5886EEA0A360D9FF1",
                "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFGRfoABEACdO+SPazdXyWRnK6JQmDvwL5Vfmp4bxK3fzM6JFO0X6B6T8Unj\n5bLyUM3+K7Cwp4x1uANo60X5k6zMJFqxFVbIdXearfU0DyGWG3DINGsIwf1NNkuA\noj3QVcv+jhigpn1wZvDT8AyJqaEisUddREUw1CpvOdCFw1uIFfodz5GJmVXZnApN\n27BJKNnsJtL8lWrUvTY/n4afXgMZ78ZH8aOkdmJ7wmVbIhrZlHu4UHJP6DbCm/+D\n7o74ozWCv6si9bfBpG6UbCxVqaeRYjb1kGT0y36TLy8W6+JXw+yISgKTORETTjQX\nzzHP5gfLu8ZTJhSvMV+xkpxc0HaX6P80rQR40QfVYRgO1uZ1Bfab+rPdUrQSPdnb\ntN6Rh6rN0QfucuqPYpiS8AJl1Si9ztyIdkYLJTL/CseO6SWDc/krIj8mX4VbN0h0\nYwECCbtv5uX8q3Jhkc8oTjpW+DRxfb1UW7us1nOoXVj9aOQaUM6QZtbVz0qQDJ9e\nSOqIx2tv5qToTxKim8E9HjX+NCvZKDIqvaoDpreMHkFP/Fo0t0tnbHTZAWcUMaih\n5WNqrFqpGYm1fDfYDIL9m3DPVaFHk3eO7apxQXwDrckeRY7Bma+YLOXG4yVf/If6\nKedgBz0Nx1gZcU6c10Fy3Dn90jcjYtTOtrEsVORdfE/1SVBKmAOjpYirnQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8MldXQlhaRlo1Q1RYSkVCQzZYQUNZUVhMWlNN\nNEdCUk0zUVlZWjJMR0VPQUxQTEZKSjVCR1lPSzRZUzU0SktYSlQzTlhVTkpLQ0VH\nTFU2RFVQUldGWEM1WlEzRk1UVFhDM0VSRlQzWT0+iQI3BBMBCgAhBQJRkX6AAhsv\nBQsJCAcCBhUICQoLAgQWAgMBAh4BAheAAAoJEIhu6go2DZ/xLcgP/1lEL1F7hoQr\nLQm8T/DqjoExh0F8am9SKb2lH9HSBUJPY9b/oPjptxyg/3NlGXP/GJGcI6SVXtnq\nGU2D2+vMUUrnV/AemAtBUIquIXMEujbGdKOuWTBCntgj6PJL6/VNi2o+v9FxATN1\n6hefcdOIk7DMaK8y56BJA+aI/7TnCr1ndHLUMXh0rKd8GSl3vXtv2kuY8iSqiOmj\nuOtW1w2lByFBglNLgnozdbudwwVqNvKX8j3oWJKsJ525Y3HsWka/l4GbkowveUYR\nU66usAX6KS1zT01pLDmYFCL7lX8SPkZq97qHoFa1C9NIHW2gP+y8Q922E9QWBqy7\n/g30ZF73MgZCOnFOChswH607LBvMGUyz+A2Qjpd7Zvf67G33inY7QlGkMI59Zz4T\nXXv/1U3Gl6LLkwGWrTDhqHgK2KA9+B6gPYDV9xh/1HTvLBE4Wf8EHhtUyW1ZxzY5\nuXvZt5OH/UKpuhcsuN6c/5+QQk0i85jTBPXm7/0XcbbRuBTnl6CiVM8vGuaLjOdW\ntAlRmX9hS7jmdE9e3Yl17qUPwlEEKSFH8Z6GgEEommoHPsgmDrQxUS6v68zfcmf3\nAE+dfKUDfC7muZfZQ0YaqeHMrDyLozRIjVtx6P3fxZPZfUvfrV4guJOVOMwi+Z1F\n5UrZB6IrSA4njr9Vr+Fb0p+v73pfV6NT\n=e+yq\n-----END PGP PUBLIC KEY BLOCK-----\n",
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
        "fingerprint": "8C71EA66B0278309A31DBD691733DA655854DB12",
        "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFGRfoABEACf5Y+6prky4JcWmKSsuh/52ZLw1FTCqrgAIK0QVFZ+cy2riFHv\njQXYB4bPOCt7PmYbmMxxIWkXqJCaPVkLbpi7p5X2Wkgh+qGgjIjotq2Y9iPP6KQ3\nGvJdpG3rWwbOsrt4rDh/L/lStn+ty4io3cDr7l7ISOtOcmOPKeKv6eGxSmCAYsnJ\nKKsIWcSjfb82KhCzL/BBApqXt9uc6Jqjh1RPL3bGIG0tq37yX/zbFefDBDF8m8d6\nc7pvvYMaO90PGViBVg6hh8+rPq/rK7YyHOWZlt6MXw7cm/GaH+DkGxGKe8Yuj92R\nOPNQFfpAI/tXldEcEvdG/4mba7uxrEMe33tsnbQamFZtXFAIrSjXa9O4CEEWnRCz\nNE90u9FeM4bk/lModsr7gOrWbO6QwctVt/YnvI7blUXzpMzDsbgvR89auKS9VHGZ\nY5L3yz0yVwRAIw3/CwsJEYajKiPadcExhZhc8OCTTe8zPXxQ8OWrvmFBA6x6cfvq\nSqoH3NXrDVY/6w9dCqVXitcYynATqm0Qkkr81jXE3BEfx7AQPXHXGasvFM1mqeQU\n+WQPqUKheomy7/7z3heasKub3MYLkuW6y7c31z6cmvt6h5fYcNPvQXCox4BJkVcK\nPbzst612sbqhTQEeSsDnVU1sPLxpfbxFfKuWQlEV8kfm4JsMbryqG9Z0RQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8UFlNR0IzRE9BNVFLVFozNjVPUTNQWUpDMk9a\nQ0RXQjIyM1dFS1Q3V0o1NDI0QUZUT1ZFSjI0SEpaSFRYQTZTQjVGUkFBVjdHRVFQ\nS01HQjQzUUxMVzNTRUxFWENYWklVRk5QWTU2WT0+iQI3BBMBCgAhBQJRkX6AAhsv\nBQsJCAcCBhUICQoLAgQWAgMBAh4BAheAAAoJEBcz2mVYVNsSQ88P/3e54noTBb/O\nFVVNYw5oY9zIQPsoYUkCCvKCv26bi3qpfsDWjohyupKLth9AfFBTk3oiNhzeFhiv\nZ5RbLgJYAWuzWNdMCSd3RAqZbbzFx3255oR9t+/RNwjeOqKpoO313myAKsRR1z+N\nbRF0A1C8GiMOCrvV/9p+rsTDrv+8fXkrQz55nGkt6JlI43EqlH0Eg7wxI+HMgTdz\nsPWBR63INNhkrR5Ln7YShOBmnUWjpEjFYvZlAbzkMbbfznDZ2g7auRpT0S8vNgcG\n9k9dG3gpMFnHiaE4SmdOIb82qv9X6Q7Owwxmz85JAe/P/CYsndUbRHSfXMp16igm\nj0RfcC7J0E/SkwBY9jc+YtGCWfqqXa1a4uY03vN1YqqFWqb+exa/Qv14wwgcS17p\n8O/X1y9gPV0qleikFgNt8sPd+a2lVdRSjh4Xh7l6eTHMqoDUJXtFu0evSg3oBFZj\n8OIXe8KZltJCYlxN+1/xlvZjAVfmYT6kxOXYsPB3o3Z9Hemgsw2PnjI04ZMwTSyb\n101xfgB1XBd1Hrv9WQ5PNoPwXRhx7/bfzQWTx/uP8luT6yqEerLiF0m/ShvYvKQa\ncLuwtW3Rlj1BD5CpdG+491jJ6cRXq8xfYmCd2MmBTtMAoq4DobYw75NKIssZ5gs6\nu6NXuCWOsf8lQNBKxkNpuohLlTef8n1y\n=Zp4Z\n-----END PGP PUBLIC KEY BLOCK-----\n",
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
              "journalist_first_name": "Bob",
              "journalist_last_name": "Smith",
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
              "journalist_first_name": "Bob",
              "journalist_last_name": "Smith",
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
      "journalist_first_name": "Bob",
      "journalist_last_name": "Smith",
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
              "journalist_first_name": "Bob",
              "journalist_last_name": "Smith",
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
              "journalist_first_name": "Bob",
              "journalist_last_name": "Smith",
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
              "journalist_first_name": "Bob",
              "journalist_last_name": "Smith",
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
              "journalist_first_name": "Bob",
              "journalist_last_name": "Smith",
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
    "first_name": "Bob",
    "last_name": "Smith",
  }
