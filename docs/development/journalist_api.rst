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
      "token": "eyJhbGciOiJIUzI1NiIsImV4cCI6MTUzMTE5Njk4MSwiaWF0IjoxNTMxMTY4MTgxfQ.eyJpZCI6MX0.TBSvfrICMxtvWgpVZzqTl6wHYNQuGPOaZpuAKwwIXXo"
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
            "add_star_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/add_star",
            "filesystem_id": "6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY=",
            "interaction_count": 2,
            "is_flagged": false,
            "is_starred": false,
            "journalist_designation": "tight-fitting horsetail",
            "key": {
                "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtDtxcBEACaduNhYLXGe3brGRpSFeIe7j6hBVGCfDjfRV0KL2u8VUPIfKIZ\n4kkCtqdfTyTObSPxaTvd20LF+ENI9konXQAf2pBGxFBLRHx0cqwSlHvc6OjCJuXI\nmG94tPThMrw5xLgvhih8/PzdUvsC7vswMp5uAK5jIVam25pXJgjCtivEGVFars0q\n4H5ti3r3GHKhHA7ictjBesTDOiRT0NkCDPDjxv2V+AlNPjfFzf5lPw1zSFVZ5A52\n1OzgadqTZfj+/aZQcQkUA8omoTlcSJI4Mf/Dvn78j4A9bJO643U54rb8Nknnm2u8\niA4RTiGo0uTifZ1Q17tDJBlRTgheH4zrx8LJzEKY1RJDQt2K5RcHsU41TdbDVtbO\nRP6RX/xYRgNzyhUue3Vn3LtMzjmkbti3tiOtIAqUMgKuA6KTNY1uViDgF0hcgi6H\nzIWsoYBZx7RJhK5nEowmddTbN+Fp8gOoUhbCyKFo+f7W6dgVDl8KKJbUapaZpMnr\nk5ldS768Q2KqArSarZTCkUPSYHMvqBGP7ZR1l0HUY4qL1WGtibq3fTE/GPdyadc7\n98slu5/30prXgsV4/mTwWvBZQlixNSM0Rdw69sannDvtRfnH2ocF4oQKOf2htwQ1\nbLvknlOXvXZEy4ctu0FXoZUFjgXHPU5y7+XaxCfspfNSFB+xhzs8FWK9ywARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8NkNIQUQ3NFlVV1RZQk5FWVU0RFlSNlUyTExO\nWkdaR0hBWkFCNU82UjVXSEQyRFVGRlpTU05LS0lETk1BV1FXSUszQUFLWUo0NzdR\nRUc2UFJJRDVDUDJSUUoyU1dDUDNJTlBVNlhHWT0+iQI/BBMBCgApBQJbQ7cXAhsv\nBQkB4MqpBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQcNhgsP2ye/LjVw//\nXe/iXqAoJMc0o2x+/1Z0xyHP/uqy2nJ/ClVibhvwwDUoDGZb3l+1KZGqF9irdhOU\nXAE/N0taKG6LSAckW9I+2nXpUSNH4iXv8uwzW6VsNAY+BSmgRnS/KLsSr6DDFHek\n5zs6gftUYQoTOdpL3CxczGDnh2tJeJmGJcobAiCj8jArlLZhtK2sYHKEBDGW67rT\nskOTuRtRNYCDiOo/0WycD4AKtlZNCI9Az4Sn5Zq9ODlzwBKx7j2CdykKXeTSxqdd\nGZQc4+CD6xempUp2SKsacIhoQKfAw6q8L6pxcc3AJDtImCQJ7qNrEcLQCafQpLhx\nObXeDPNruxLHL+70rpIUs7bj5+ChZUwcfCzuT3bEqpKHCq+8vfpHJVgopUI1gg3G\nr88U6REdXobAQqh5AN3AFYFdg9P4XiFIpAnp7vCWkGGGULEQ0vnTZcASSdbj+MRI\n8v1qk0lZOMOn9JYYc3dePq5okZhfMqPOubEwaji8FDTOmhWnQiigIx8SS/XhQonY\nxJ14xgRoWCqwdBjrrjmJf+OScfJBZvFchf7mwkPkOUrdHCgUkWzGaUI4TLmh9xSk\nTy8fScG/U4JVlH0V8/xY01DOXvGRo3DAEn3ptm+j48fI1coH7jy0n9pQW4r2BNqX\n5MokpDpo3g5AaQr54IV1KBcetYBy301GxIytGaYThn8=\n=b/Mq\n-----END PGP PUBLIC KEY BLOCK-----\n",
                "type": "PGP"
            },
            "last_updated": "2018-07-09T19:27:17.879344Z",
            "number_of_documents": 0,
            "number_of_messages": 2,
            "remove_star_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/remove_star",
            "reply_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/reply",
            "source_id": 1,
            "submissions_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/submissions",
            "url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D"
        },
        {
            "add_star_url": "/api/v1/sources/VITB6XPYQS3MB2HFEGF3NZYD5G5ZMGMOA2VFKETEGYYKDAY4DFI53ZJMNGCZKWMG2SON7XAUXNRWEURNJ2OVY4QJPGGMGO4TDMMWFSQ%3D/add_star",
            "filesystem_id": "VITB6XPYQS3MB2HFEGF3NZYD5G5ZMGMOA2VFKETEGYYKDAY4DFI53ZJMNGCZKWMG2SON7XAUXNRWEURNJ2OVY4QJPGGMGO4TDMMWFSQ=",
            "interaction_count": 2,
            "is_flagged": false,
            "is_starred": false,
            "journalist_designation": "existential irreverence",
            "key": {
                "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtDtxkBEAC4XWuphmzqLCvMf86u6uoIAV5iKdcP8N3xlfmMEtu6I5gFE3+8\n4IOCWbAUcXLqhDY8RjId+gWoKIQZC0n9PDuF04cout6+F+nHlfm8Rx760mSPPTNW\nT9Gk3UtnJlMG+V6vPoiZpIb21rVgBg+7BuvVXyAc/nwiiCUeV/AFGwBMf6MKerCj\nmmo+nfcjJAAfep7NZH/YYEpwoQ9lxWjHn+8pQh9MI5FRur9XGv1+o244SaVHM/0w\n17S6AbPco67S8xyFMO5v88y5dUkJSsN72FX+dTS5Scurdl6J/KNvi4fzBZWg2VTu\nsT99OSOWTjXHX5bcR+43E3U+godOOLtzzfS1TIlAP4Xp+DvXMLwk33Vo73AWAv//\n9IVmk1hVOpmA37AEho9SfbIH4rvEi7aYesk2As5VIY47dIPrAPlf2GC6sTEXeVyJ\ncSEz4fWuMrbw4XtXTOHnf2zSwD8AteUtOcj83OXmLMAqtBFoXGv5Y0XakPJt5RYQ\nzZy6P77ULAKsqC154AkzaWGiQ8UmRhK1aHi3ks3PT91XmN8NYHTTgxRJGXI7gzkj\nn582Ix2EzuoJE16r05Z0M01ggwm1Z2ugHP8ningvCBq0cqpzad/bjF2iX4+pi8um\nuK57rky3Ci4hpDfaSR3CCZb7SNqdkFthKlwaGNOUIn6mBjO56MiXWIY2OQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8VklUQjZYUFlRUzNNQjJIRkVHRjNOWllENUc1\nWk1HTU9BMlZGS0VURUdZWUtEQVk0REZJNTNaSk1OR0NaS1dNRzJTT043WEFVWE5S\nV0VVUk5KMk9WWTRRSlBHR01HTzRURE1NV0ZTUT0+iQI/BBMBCgApBQJbQ7cZAhsv\nBQkB4MqnBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQXFiwg/uZ5dM+sQ/+\nI7WBIFEcLC9PLCl96mmx2ena9jXYgF+QEkjFBkzOuKwcb70N9ViDzbQBYlfLd1y2\ngbfxRd2l4ODi0j3C8eaW8Iyn8518rZICVMzJPJIEr4RbOui2ykCTEy0SVa/XXbw9\nsNn1auyqUwVxI89HGd7K2yfnN5GFVKhrNRS78v07cGau5UKb+ky6WuyJQ8o+VNRM\nsFXVKYxUEUC9EaDoF55mDvxaNd0v2HG+SGVRmnNj64EvRE/o2Fk/vAozw4gbfL2s\nRyZ8Yl/3NK8bcea8fD7eRwfkVIyRsON8J6XrYmkimrCzi9a+XUH0Zg4YTmXo5COU\nv+poxkdtRxHq1stKYjngOhEnfOfsRf0KHO+yt1RgLs7yS53tNu1P2fQj4ND4yGVo\nHPA772x9Khc9ycM3RItW6JQEJKyoRz9KeTVERni+J0j8MGcGRx+0rLr6dpjrbdQY\nKHK/7i17F2yP7kpG4dSqHb1dRw1x5rBng69kEgaEum22oE69w5oiYGrMihSQtHCw\nzHf9ToOeMiJ5VBrl8obaAJUH+UoQxQD1LSiK1TNlNTA2Q+4z5AqCY3biLXpVFZdO\nlOrfoMRsXGYgxOWYJ7rhHk5zJlkU4pRiywcoSsAQ/mQj8D3Ar0mIqeXoExjseGS6\nAI08meR/2HO1G9XycrBcZfMMkHsnigD2InUdDCCxzlA=\n=HqmY\n-----END PGP PUBLIC KEY BLOCK-----\n",
                "type": "PGP"
            },
            "last_updated": "2018-07-09T19:27:20.293592Z",
            "number_of_documents": 0,
            "number_of_messages": 2,
            "remove_star_url": "/api/v1/sources/VITB6XPYQS3MB2HFEGF3NZYD5G5ZMGMOA2VFKETEGYYKDAY4DFI53ZJMNGCZKWMG2SON7XAUXNRWEURNJ2OVY4QJPGGMGO4TDMMWFSQ%3D/remove_star",
            "reply_url": "/api/v1/sources/VITB6XPYQS3MB2HFEGF3NZYD5G5ZMGMOA2VFKETEGYYKDAY4DFI53ZJMNGCZKWMG2SON7XAUXNRWEURNJ2OVY4QJPGGMGO4TDMMWFSQ%3D/reply",
            "source_id": 2,
            "submissions_url": "/api/v1/sources/VITB6XPYQS3MB2HFEGF3NZYD5G5ZMGMOA2VFKETEGYYKDAY4DFI53ZJMNGCZKWMG2SON7XAUXNRWEURNJ2OVY4QJPGGMGO4TDMMWFSQ%3D/submissions",
            "url": "/api/v1/sources/VITB6XPYQS3MB2HFEGF3NZYD5G5ZMGMOA2VFKETEGYYKDAY4DFI53ZJMNGCZKWMG2SON7XAUXNRWEURNJ2OVY4QJPGGMGO4TDMMWFSQ%3D"
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
    "add_star_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/add_star",
    "filesystem_id": "6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY=",
    "interaction_count": 2,
    "is_flagged": false,
    "is_starred": false,
    "journalist_designation": "tight-fitting horsetail",
    "key": {
        "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtDtxcBEACaduNhYLXGe3brGRpSFeIe7j6hBVGCfDjfRV0KL2u8VUPIfKIZ\n4kkCtqdfTyTObSPxaTvd20LF+ENI9konXQAf2pBGxFBLRHx0cqwSlHvc6OjCJuXI\nmG94tPThMrw5xLgvhih8/PzdUvsC7vswMp5uAK5jIVam25pXJgjCtivEGVFars0q\n4H5ti3r3GHKhHA7ictjBesTDOiRT0NkCDPDjxv2V+AlNPjfFzf5lPw1zSFVZ5A52\n1OzgadqTZfj+/aZQcQkUA8omoTlcSJI4Mf/Dvn78j4A9bJO643U54rb8Nknnm2u8\niA4RTiGo0uTifZ1Q17tDJBlRTgheH4zrx8LJzEKY1RJDQt2K5RcHsU41TdbDVtbO\nRP6RX/xYRgNzyhUue3Vn3LtMzjmkbti3tiOtIAqUMgKuA6KTNY1uViDgF0hcgi6H\nzIWsoYBZx7RJhK5nEowmddTbN+Fp8gOoUhbCyKFo+f7W6dgVDl8KKJbUapaZpMnr\nk5ldS768Q2KqArSarZTCkUPSYHMvqBGP7ZR1l0HUY4qL1WGtibq3fTE/GPdyadc7\n98slu5/30prXgsV4/mTwWvBZQlixNSM0Rdw69sannDvtRfnH2ocF4oQKOf2htwQ1\nbLvknlOXvXZEy4ctu0FXoZUFjgXHPU5y7+XaxCfspfNSFB+xhzs8FWK9ywARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8NkNIQUQ3NFlVV1RZQk5FWVU0RFlSNlUyTExO\nWkdaR0hBWkFCNU82UjVXSEQyRFVGRlpTU05LS0lETk1BV1FXSUszQUFLWUo0NzdR\nRUc2UFJJRDVDUDJSUUoyU1dDUDNJTlBVNlhHWT0+iQI/BBMBCgApBQJbQ7cXAhsv\nBQkB4MqpBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQcNhgsP2ye/LjVw//\nXe/iXqAoJMc0o2x+/1Z0xyHP/uqy2nJ/ClVibhvwwDUoDGZb3l+1KZGqF9irdhOU\nXAE/N0taKG6LSAckW9I+2nXpUSNH4iXv8uwzW6VsNAY+BSmgRnS/KLsSr6DDFHek\n5zs6gftUYQoTOdpL3CxczGDnh2tJeJmGJcobAiCj8jArlLZhtK2sYHKEBDGW67rT\nskOTuRtRNYCDiOo/0WycD4AKtlZNCI9Az4Sn5Zq9ODlzwBKx7j2CdykKXeTSxqdd\nGZQc4+CD6xempUp2SKsacIhoQKfAw6q8L6pxcc3AJDtImCQJ7qNrEcLQCafQpLhx\nObXeDPNruxLHL+70rpIUs7bj5+ChZUwcfCzuT3bEqpKHCq+8vfpHJVgopUI1gg3G\nr88U6REdXobAQqh5AN3AFYFdg9P4XiFIpAnp7vCWkGGGULEQ0vnTZcASSdbj+MRI\n8v1qk0lZOMOn9JYYc3dePq5okZhfMqPOubEwaji8FDTOmhWnQiigIx8SS/XhQonY\nxJ14xgRoWCqwdBjrrjmJf+OScfJBZvFchf7mwkPkOUrdHCgUkWzGaUI4TLmh9xSk\nTy8fScG/U4JVlH0V8/xY01DOXvGRo3DAEn3ptm+j48fI1coH7jy0n9pQW4r2BNqX\n5MokpDpo3g5AaQr54IV1KBcetYBy301GxIytGaYThn8=\n=b/Mq\n-----END PGP PUBLIC KEY BLOCK-----\n",
        "type": "PGP"
    },
    "last_updated": "2018-07-09T19:27:17.879344Z",
    "number_of_documents": 0,
    "number_of_messages": 2,
    "remove_star_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/remove_star",
    "reply_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/reply",
    "source_id": 1,
    "submissions_url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D/submissions",
    "url": "/api/v1/sources/6CHAD74YUWTYBNEYU4DYR6U2LLNZGZGHAZAB5O6R5WHD2DUFFZSSNKKIDNMAWQWIK3AAKYJ477QEG6PRID5CP2RQJ2SWCP3INPU6XGY%3D"
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

  DELETE /api/v1/sources/<filesystem_id>

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

Flag a source [``POST``]
^^^^^^^^^^^^^^^^^^^^^^^^

Requires authentication.

.. code:: sh

  POST /api/v1/sources/<filesystem_id>/flag

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
    "last_login": "2018-07-09T20:29:41.696782Z",
    "username": "journalist"
  }
