# -*- coding: utf-8 -*-
from journalist_app import create_app
from sdconfig import JournalistInterfaceConfig

config = JournalistInterfaceConfig()
app = create_app(config)


if __name__ == "__main__":  # pragma: no cover
    debug = config.env != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)  # nosec
