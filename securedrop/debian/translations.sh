#!/bin/bash
set -ex

# We create the virtualenv separately from the "pip install" commands below,
# to make error-reporting a bit more obvious. We also update beforehand,
# beyond what the system version provides, see #6317.
python3 -m venv /tmp/securedrop-app-code-i18n-ve
/tmp/securedrop-app-code-i18n-ve/bin/pip3 install -r \
<(echo "pip==21.3
--hash=sha256:4a1de8f97884ecfc10b48fe61c234f7e7dcf4490a37217011ad9369d899ad5a6
--hash=sha256:741a61baab1dbce2d8ca415effa48a2b6a964564f81a9f4f1fce4c433346c034")

# Install dependencies
/tmp/securedrop-app-code-i18n-ve/bin/pip3 install --no-deps --no-binary :all: --require-hashes -r requirements/python3/translation-requirements.txt

# Compile the translations
. /tmp/securedrop-app-code-i18n-ve/bin/activate
pybabel compile --directory translations/
