#!/bin/bash
set -ex

# We create the virtualenv separately from the "pip install" commands below,
# to make error-reporting a bit more obvious. We also update beforehand,
# beyond what the system version provides, see #6317.
python3 -m venv /tmp/securedrop-app-code-i18n-ve
/tmp/securedrop-app-code-i18n-ve/bin/pip3 install -r \
<(echo "pip==24.2 \
--hash=sha256:5b5e490b5e9cb275c879595064adce9ebd31b854e3e803740b72f9ccf34a45b8 \
--hash=sha256:2cd581cf58ab7fcfca4ce8efa6dcacd0de5bf8d0a3eb9ec927e07405f4d9e2a2")

# Install dependencies
/tmp/securedrop-app-code-i18n-ve/bin/pip3 install --no-deps --no-binary :all: --require-hashes -r requirements/python3/translation-requirements.txt

# Compile the translations
. /tmp/securedrop-app-code-i18n-ve/bin/activate
pybabel compile --directory translations/
