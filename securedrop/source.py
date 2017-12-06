# -*- coding: utf-8 -*-

import config

from source_app import create_app

app = create_app(config)


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8080)
