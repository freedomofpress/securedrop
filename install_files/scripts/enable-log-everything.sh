#!/bin/bash

#Enable source interface logging
source_wsgi=/var/chroot/source/var/www/securedrop/source.wsgi
apache_source=/var/chroot/source/etc/apache2/sites-enabled/source

sed -i "s@ErrorLog .*@ErrorLog /var/log/apache2/error.log@" $apache_source

sed -i "s@LogLevel .*@LogLevel info@" $apache_source

if ! grep -q 'import sys' $source_wsgi; then
    sed -i '/#!\/usr\/bin\/python/aimport sys' $source_wsgi
fi

if ! grep -q 'import logging' $source_wsgi; then
    sed -i '/import sys/aimport logging' $source_wsgi
fi

if ! grep -q 'logging.basicConfig' $source_wsgi; then
    sed -i '/import logging/alogging.basicConfig(stream=sys.stderr)' $source_wsgi
    echo 'updated logging.basicConfig'
fi

schroot -c source -u root --directory / service apache2 reload
