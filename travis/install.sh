#/bin/bash 
set -e -u

pip install --upgrade distribute
pip install -r securedrop/source-requirements.txt
pip install -r securedrop/document-requirements.txt
pip install -r securedrop/test-requirements.txt
