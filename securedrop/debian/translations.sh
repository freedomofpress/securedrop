#!/bin/bash
set -ex

export PATH="${PATH}:/root/.cargo/bin"

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

# Compile the translations, need to have a placeholder config.py that we clean up
export PYTHONDONTWRITEBYTECODE="true"
cp config.py.example config.py
. /tmp/securedrop-app-code-i18n-ve/bin/activate
/tmp/securedrop-app-code-i18n-ve/bin/python3 ./i18n_tool.py --verbose translate-messages --compile
rm config.py
