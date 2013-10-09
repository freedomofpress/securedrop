node basenode {
#These values are modified by the deaddrop install script that uses spaces as delimiter
$enable_2_step = 'false'
$source_ip = '10.184.36.21'
$journalist_ip = '10.242.74.245'
$monitor_ip = '10.154.176.156'
$admin_ip = '76.169.229.227'
$intFWlogs_ip = '76.169.229.227'
$app_gpg_pub_key = 'journalist.asc'
$hmac_secret = 'long random value'
$app_gpg_fingerprint = 'E82A C40F 3158 9EA3 E73F 0C5D 0A20 6074 BE26 C950'
$mail_server = 'gmail-smtp-in.l.google.com'
$ossec_email_to = 'dolanjs@gmail.com'
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
