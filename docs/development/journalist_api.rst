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
      "expiration": "2018-07-03T02:56:22.700788",
      "token": "eyJhbGciOiJIUzI1NiIsImV4cCI6MTUzMDU4NjU4MiwifWF0IjoxNTMwNTc5MzgyfQ.eyJpZCI6MX0.P_PfcLMk1Dq5VCIANo-lJbu0ZyCL2VcT8qf9fIZsTCM"
  }

Thereafter in order to authenticate to protected endpoints, send the token in
HTTP Authorization header:

.. code:: sh

  Authorization: Token eyJhbGciOiJIUzI1NiIsImV4cCI6MTUzMDU4NjU4MiwifWF0IjoxNTMwNTc5MzgyfQ.eyJpZCI6MX0.P_PfcLMk1Dq5VCIANo-lJbu0ZyCL2VcT8qf9fIZsTCM

This header will be checked with each API request to see if it is valid and
not yet expired. Tokens expire after 7200 seconds (120 minutes).

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
            "add_star_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/add_star",
            "filesystem_id": "S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA=",
            "interaction_count": 2,
            "is_flagged": false,
            "is_starred": true,
            "journalist_designation": "fifty-five sorter",
            "key": {
                "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtAB7UBEAC7xcsW+IgHTVgoYOLjNLWPPySqqClbWmU3SruesHPmgt9X1JnN\nHHHVjAofFPkuUHVHqTPZcnG8YTKEu8mcLQp9nDu6rTFZka2XEhAJ39b9piwmIX7/\nPObgBS0DgfMd4aMb4tQWOTH+QzpPHYZuqDFaXnZ4cppVi5x1lxU+tCqbWSRUOpES\nrupCO5Wh5PJtULUZdcEhe38aST7JCnl/FZWwlh4+uQLXqFUhV5mphGwYk+DIz/8c\nhDsf0InXTiZcivHJb9/kefFwsy1nWSXBs8Cu/T5br0iTl9OFUpuXirlMlzUV1PkM\n182RJvtb5lO8YycEYyHO+26vND9sQIzbSMkMkaUkxe8jD0DCf2Jo5CpEQQ76ft8W\ngsPl9Wuts9gH0p/xdaUZCOprLH7A0Eyp4LDrpVMqshUqmQvNuF1UiKhDqjOzA123\ncrvJZIjD1IxH7FGuZCDGjxAhvTfvio5MF2MLcKIsM5OK94Gor46rduxwitHahPUY\n1FgVTMM1PK3cGoHn+kQ42fk1wpHg8IQH0oKM4VYzOy7oWIoLALFbEA2ODW/MiDMC\n+RdkYwTaw+KuhUUt0DRPTOu8ZY8Id1lH/8b5UdKuPs4rg7RK0wtzszMCDmkK3kpe\nLYidO9mTf8ldzMVToHMQRgUAZ0jkPovtx2QHgwayHV5K9E8kfjjitrjZzQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8UzdCQkZMNExWRkVXMjZHWFA2QlFFN1pKU0tF\nQzNXSUZGQkNVWE1WTTNWRUVTQzNZNFhETVlaU1Q0VURYWVhIRktRWUQ3SVZDNUFH\nM1ZMRVlINUJMTzc0SDJWT1M0MlJLM1U1T0NIQT0+iQI/BBMBCgApBQJbQAe1Ahsv\nBQkB4dcLBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQIci5eVVVBoiQchAA\nuXET3PAkrDAQ3i4sLRkEQ42gqgmUX+QgYyIYzfQm6QpQRHovHY0HutYY2uuqM+vc\nKU+bEPWTD3y2p0bcfO7xyGBq35gnrkV7aC9edRO6Cyz4WPYhiSsjyQ5WXbHhDB5n\nI9RccxVFxTnlVet+TQFU8rX3djkKUI37Pq1O7HwHfPA6rrnR2Y6/OhS0KpWgVWow\nCt1lZoYro2GB5cghkdFbOsvRdoZWQMzYm2BH5EPoBFX+h1i4JPjZZwlDYsi79GqH\nG/KYY3BGqrgk/7Z/Arc45hw3Qo/R8L1xlj24Yyx9jOHQUR+TuUqrIMvXr0nGemU3\ntUy5FzqJH/wMGWKqvryuq4jOZYykZrmv3ogS1aiZiwYBkr4gY1KRjwb1Z3Hh4gyE\nu6VJXZ1BX2mqm0WOamIyqwG9pyvPdDE1EbjUAqdGZiXYIVznsc1xqhOLSAZF2lrO\nfMORxu8O6vYzJWGGnKnu7eC3Fw/nzyqkCwA9Q2Dmwd6brZNhu8cQKP98+HkIzVja\ndxTOZn8AARbVpzxbc0L5k8yyoqwon8OohbU2+K7OZG9uk/1DcSBCLyWk++yYnSng\n/GhncG1RRU9NY6vFs2AB/nxT+JKi4sUG7I890qh9PrRXwfKtHCcIMw5mc26aEnnq\nFEHSg9czun/Aw2qwuJf5EsveBUAWPSBr9nzjdvbERjI=\n=2Ie1\n-----END PGP PUBLIC KEY BLOCK-----\n",
                "type": "PGP"
            },
            "last_updated": "Sat, 07 Jul 2018 00:22:12 GMT",
            "number_of_documents": 0,
            "number_of_messages": 2,
            "remove_star_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/remove_star",
            "reply_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/reply",
            "source_id": 1,
            "submissions_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/submissions",
            "url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D"
        },
        {
            "add_star_url": "/api/v1/sources/VY3FJLGRS2DTCEMBYHQ7DU5SM4EBZQZOIASPUEN2IPOLGLZKSATQJWPCRYRP77ELOFC7NJXI66X3IPJPHL6WAQ4ZJEA3NFB3GCXRXWY%3D/add_star",
            "filesystem_id": "VY3FJLGRS2DTCEMBYHQ7DU5SM4EBZQZOIASPUEN2IPOLGLZKSATQJWPCRYRP77ELOFC7NJXI66X3IPJPHL6WAQ4ZJEA3NFB3GCXRXWY=",
            "interaction_count": 2,
            "is_flagged": false,
            "is_starred": false,
            "journalist_designation": "phobic interception",
            "key": {
                "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtAB7gBEADNlPnQ4wdWWmYLfoUFmDdVdH9j4nj6+l0NuQIfZBigdglnsKHb\nXWNJ5ay2ozT8oJSjmoKb3gDFrLeIrelibav/jBAelonEfxupmkRq9C3Tw6scKXcp\nyv1LTFK14Lc4p7OOyPA5lQXL0S3KEsRG1tfxVT0rVSCC7dWYz2t1W+aoIJGNvz0c\nlSFGzR7jc5AFXFfZTc9Jh95I7eLk7KjQQf5MTnGXyZMQF4Xltvw3yXTzYEAXt0Ox\n2qWj+P2hXrbiqaOJaPdJQ5+KrmWpWsx86AVHK9Paj56fgyl86V8l+tolnVqW0YEx\ndvGrfyico8pYm9MFqby7xQlkJ3ubfvI365ZjLg6NF0CMNlco/cTVsbxJ6jvZVa71\nFqGXggNPDyaa6qqGLaD6O/B6rw5pKNSejf1Q/0KPxvQ27Aq4eMDNiwVBoGxCAytc\nlM76rM2v5dxp/XUpUVb8A0MpyleLTol2UToCslCy0bJWmK7Z4fmAgB/x+oD8nmbm\nBiZWTNHrOixpGfyEb51ukbXAeEnwONCTjU5gsotvSB95ZwKcUE+pHcibZyhJCZ9M\nUb/Tzl3CSdxCW77XcHXV4/FL0Kk7YIiEHhrNq3PL/Vh4mIwNaJPkMcgEHknVyDkU\nAG6rqkQiPCVGQOOYQIQGfx1+RWfDY5VTWStsKLgVoMm+FCaR13Q68NcCuQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8VlkzRkpMR1JTMkRUQ0VNQllIUTdEVTVTTTRF\nQlpRWk9JQVNQVUVOMklQT0xHTFpLU0FUUUpXUENSWVJQNzdFTE9GQzdOSlhJNjZY\nM0lQSlBITDZXQVE0WkpFQTNORkIzR0NYUlhXWT0+iQI/BBMBCgApBQJbQAe4Ahsv\nBQkB4dcIBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQIrDFV3/5lPdTGBAA\nqiS73BGiiGl/93CCEmz9OWblAdvMzRR5GsZLaAOF3bUxnMER0F9nlzID2ckYQ2RT\n0+6iJpaTuRNGwnoKfwmoZ39zvWFsGKaXbjU0Aaj5BZW0tL4043wb8gInoLYp1Gmt\niXz1lqWH5M40CVUMD6xXsVtuV6UnCBtsx3ye4X/KdxCWsWCm6kd60GFkuNMMolno\nEFIsnAKTo+ecofwrfUn4kVaNmH/FwTTUyq8U2WtZDPS9RTs4BA4XsttMer1KkyKN\nvNYQkTx9tiIR2dFasIaLyFGbgJ1O9iNMyBwp85LpSSLJDz7iMp65u1/mSFd4KD0A\nnvkYoBJ2P+ds2C1nRd7lZxnwXJ9kKD1SiMMZBemoC15BP2HsHWFSQKv/ZN/E2RhV\n8Uj3Zrrxb4a+KrCJVw9FW0vtStJkDyXroizXn3Zln5HIqus7bGw18c48lc4IqdQH\nPgq2do8bvhDVP6eNsWiTfu7hs1YOlYLeB9sn5ffkT6Ujz9O86nE3F91DS/dtn9tn\n5Evd/QTVTJKPxOYus3WRJGvqw09RAqf8XI5iVOTqVv21SyjDUEy5xf0CvwuYJ0c7\nXJ+BGJdLwP7cHdGth0Gwfn+PgvjgJZOYrttn/rMQqy5j5wcu8dtpqxcvEyJhevpF\nm4VRGVb9gzIIG1/RHSk5qQRQ1sS/LHZj6ySy21Iq7B0=\n=oGey\n-----END PGP PUBLIC KEY BLOCK-----\n",
                "type": "PGP"
            },
            "last_updated": "Sat, 07 Jul 2018 00:22:14 GMT",
            "number_of_documents": 0,
            "number_of_messages": 2,
            "remove_star_url": "/api/v1/sources/VY3FJLGRS2DTCEMBYHQ7DU5SM4EBZQZOIASPUEN2IPOLGLZKSATQJWPCRYRP77ELOFC7NJXI66X3IPJPHL6WAQ4ZJEA3NFB3GCXRXWY%3D/remove_star",
            "reply_url": "/api/v1/sources/VY3FJLGRS2DTCEMBYHQ7DU5SM4EBZQZOIASPUEN2IPOLGLZKSATQJWPCRYRP77ELOFC7NJXI66X3IPJPHL6WAQ4ZJEA3NFB3GCXRXWY%3D/reply",
            "source_id": 2,
            "submissions_url": "/api/v1/sources/VY3FJLGRS2DTCEMBYHQ7DU5SM4EBZQZOIASPUEN2IPOLGLZKSATQJWPCRYRP77ELOFC7NJXI66X3IPJPHL6WAQ4ZJEA3NFB3GCXRXWY%3D/submissions",
            "url": "/api/v1/sources/VY3FJLGRS2DTCEMBYHQ7DU5SM4EBZQZOIASPUEN2IPOLGLZKSATQJWPCRYRP77ELOFC7NJXI66X3IPJPHL6WAQ4ZJEA3NFB3GCXRXWY%3D"
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
      "add_star_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/add_star",
      "filesystem_id": "S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA=",
      "interaction_count": 2,
      "is_flagged": false,
      "is_starred": true,
      "journalist_designation": "fifty-five sorter",
      "key": {
          "public": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQINBFtAB7UBEAC7xcsW+IgHTVgoYOLjNLWPPySqqClbWmU3SruesHPmgt9X1JnN\nHHHVjAofFPkuUHVHqTPZcnG8YTKEu8mcLQp9nDu6rTFZka2XEhAJ39b9piwmIX7/\nPObgBS0DgfMd4aMb4tQWOTH+QzpPHYZuqDFaXnZ4cppVi5x1lxU+tCqbWSRUOpES\nrupCO5Wh5PJtULUZdcEhe38aST7JCnl/FZWwlh4+uQLXqFUhV5mphGwYk+DIz/8c\nhDsf0InXTiZcivHJb9/kefFwsy1nWSXBs8Cu/T5br0iTl9OFUpuXirlMlzUV1PkM\n182RJvtb5lO8YycEYyHO+26vND9sQIzbSMkMkaUkxe8jD0DCf2Jo5CpEQQ76ft8W\ngsPl9Wuts9gH0p/xdaUZCOprLH7A0Eyp4LDrpVMqshUqmQvNuF1UiKhDqjOzA123\ncrvJZIjD1IxH7FGuZCDGjxAhvTfvio5MF2MLcKIsM5OK94Gor46rduxwitHahPUY\n1FgVTMM1PK3cGoHn+kQ42fk1wpHg8IQH0oKM4VYzOy7oWIoLALFbEA2ODW/MiDMC\n+RdkYwTaw+KuhUUt0DRPTOu8ZY8Id1lH/8b5UdKuPs4rg7RK0wtzszMCDmkK3kpe\nLYidO9mTf8ldzMVToHMQRgUAZ0jkPovtx2QHgwayHV5K9E8kfjjitrjZzQARAQAB\ntHxBdXRvZ2VuZXJhdGVkIEtleSA8UzdCQkZMNExWRkVXMjZHWFA2QlFFN1pKU0tF\nQzNXSUZGQkNVWE1WTTNWRUVTQzNZNFhETVlaU1Q0VURYWVhIRktRWUQ3SVZDNUFH\nM1ZMRVlINUJMTzc0SDJWT1M0MlJLM1U1T0NIQT0+iQI/BBMBCgApBQJbQAe1Ahsv\nBQkB4dcLBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQIci5eVVVBoiQchAA\nuXET3PAkrDAQ3i4sLRkEQ42gqgmUX+QgYyIYzfQm6QpQRHovHY0HutYY2uuqM+vc\nKU+bEPWTD3y2p0bcfO7xyGBq35gnrkV7aC9edRO6Cyz4WPYhiSsjyQ5WXbHhDB5n\nI9RccxVFxTnlVet+TQFU8rX3djkKUI37Pq1O7HwHfPA6rrnR2Y6/OhS0KpWgVWow\nCt1lZoYro2GB5cghkdFbOsvRdoZWQMzYm2BH5EPoBFX+h1i4JPjZZwlDYsi79GqH\nG/KYY3BGqrgk/7Z/Arc45hw3Qo/R8L1xlj24Yyx9jOHQUR+TuUqrIMvXr0nGemU3\ntUy5FzqJH/wMGWKqvryuq4jOZYykZrmv3ogS1aiZiwYBkr4gY1KRjwb1Z3Hh4gyE\nu6VJXZ1BX2mqm0WOamIyqwG9pyvPdDE1EbjUAqdGZiXYIVznsc1xqhOLSAZF2lrO\nfMORxu8O6vYzJWGGnKnu7eC3Fw/nzyqkCwA9Q2Dmwd6brZNhu8cQKP98+HkIzVja\ndxTOZn8AARbVpzxbc0L5k8yyoqwon8OohbU2+K7OZG9uk/1DcSBCLyWk++yYnSng\n/GhncG1RRU9NY6vFs2AB/nxT+JKi4sUG7I890qh9PrRXwfKtHCcIMw5mc26aEnnq\nFEHSg9czun/Aw2qwuJf5EsveBUAWPSBr9nzjdvbERjI=\n=2Ie1\n-----END PGP PUBLIC KEY BLOCK-----\n",
          "type": "PGP"
      },
      "last_updated": "Sat, 07 Jul 2018 00:22:12 GMT",
      "number_of_documents": 0,
      "number_of_messages": 2,
      "remove_star_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/remove_star",
      "reply_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/reply",
      "source_id": 1,
      "submissions_url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D/submissions",
      "url": "/api/v1/sources/S7BBFL4LVFEW26GXP6BQE7ZJSKEC3WIFFBCUXMVM3VEESC3Y4XDMYZST4UDXYXHFKQYD7IVC5AG3VLEYH5BLO74H2VOS42RK3U5OCHA%3D"
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
      "last_login": "Fri, 29 Jun 2018 20:13:53 GMT",
      "username": "journalist"
  }
