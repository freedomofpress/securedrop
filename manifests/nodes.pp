node basenode {
#These values are modified by the deaddrop install script that uses spaces as delimiter
$enable_2_step = 'false'
$source_ip = ''
$source_hostname = ''
$journalist_ip = ''
$journalist_hostname = ''
$monitor_ip = ''
$monitor_hostname = ''
$admin_ip = ''
$intFWlogs_ip = ''
$app_gpg_pub_key = 'secure_drop.asc'
$hmac_secret = ''
$bcrypt_salt = ''
$app_gpg_fingerprint = ''
$mail_server = 'gmail-smtp-in.l.google.com'
$ossec_email_to = ''
# The values in this section do not need to be changed
  $puppetmaster_ip         = 'monitor'
  $apache_name             = 'apache2-mpm-worker'
  $apache_user             = 'www-data'
  $sshfs_user              = 'www-data'
  $deaddrop_home           = '/var/www/deaddrop'
  $store_dir               = "$deaddrop_home/store"
  $keys_dir                = "$deaddrop_home/keys"
  $word_list               = "$deaddrop_home/wordlist"
  $source_template_dir     = "$deaddrop_home/source_templates"
  $journalist_template_dir = "$deaddrop_home/journalist_templates"
  $docroot                 = "$deaddrop_home/static"
  $docroot_owner           = 'www-data'
  $docroot_group           = 'www-data'
  $enable_mods             = 'ssl wsgi'
  $disabled_mods           = 'auth_basic authn_file autoindex cgid env setenvif status'
  $default_sites           = 'default default-ssl'
}

include ssh::auth
ssh::auth::key { "www-data": }

node 'monitor_fqdn' inherits basenode {
  $role      = 'monitor'
  $ossectype = 'server'

  include ssh::auth::keymaster
  include deaddrop::base
  include deaddrop::cis_debian_v1_0
  include ossec::server
#  include deaddrop::grsec
}

node 'source_fqdn' inherits basenode {
  $role      = 'source'
  $ossectype = 'agent'
  
  include deaddrop::base
  include deaddrop::cis_debian_v1_0
  include deaddrop::tor
  include deaddrop::source
  include ossec::agent
#  include deaddrop::grsec
}

node 'journalist_fqdn' inherits basenode {
  $role      = 'journalist'
  $ossectype = 'agent'

  include deaddrop::base
  include deaddrop::cis_debian_v1_0
  include deaddrop::tor
  include deaddrop::journalist
  include ossec::agent
#  include deaddrop::grsec
}
