# -*- coding: utf-8 -*-
from sdconfig import SourceInterfaceConfig
from source_app import create_app

config = SourceInterfaceConfig()
app = create_app(config)


if __name__ == "__main__":  # pragma: no cover
    debug = config.env != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8080)  # nosec
