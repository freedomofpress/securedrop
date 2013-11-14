# data directories - should be on secure media
STORE_DIR='/var/www/deaddrop/store'
GPG_KEY_DIR='/var/www/deaddrop/keys'

# fingerprint of the GPG key to encrypt submissions to
JOURNALIST_KEY='$APP_GPG_KEY_FINGERPRINT'

SOURCE_TEMPLATES_DIR='/var/www/deaddrop/source_templates'
JOURNALIST_TEMPLATES_DIR='/var/www/deaddrop/journalist_templates'
WORD_LIST='/var/www/deaddrop/wordlist'

BCRYPT_SALT='BCRYPT_SALT_VALUE' # bcrypt.gensalt()
SECRET_KEY='SECRET_KEY_VALUE' # import os; os.urandom(24)
