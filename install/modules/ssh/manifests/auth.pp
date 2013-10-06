# =========                                                 

# ssh::auth                                                 

# =========                                                 

#                                                           

# The latest official release and documentation for ssh::auth can always

# be found at http://reductivelabs.com/trac/puppet/wiki/Recipes/ModuleSSHAuth .

#                                                                              

# Version:          0.3.2                                                      

# Release date:     2009-12-29                                                 



class ssh::auth {



$keymaster_storage = "/var/lib/keys/" 



Exec { path => "/usr/bin:/usr/sbin:/bin:/sbin" }

Notify { withpath => false }                    





##########################################################################





# ssh::auth::key 



# Declare keys.  The approach here is just to define a bunch of

# virtual resources, representing key files on the keymaster, client,

# and server.  The virtual keys are then realized by                 

# ssh::auth::{keymaster,client,server}, respectively.  The reason for

# doing things that way is that it makes ssh::auth::key into a "one  

# stop shop" where users can declare their keys with all of their    

# parameters, whether those parameters apply to the keymaster, server,

# or client.  The real work of creating, installing, and removing keys

# is done in the private definitions called by the virtual resources: 

# ssh_auth_key_{master,server,client}.                                



define key ($ensure = "present", $filename = "", $force = false, $group = "puppet", $home = "", $keytype = "rsa", $length = 2048, $maxdays = "", $mindate = "", $options = "", $user = "") {                                                                                                                                                    



  ssh_auth_key_namecheck { "${title}-title": parm => "title", value => $title }



  # apply defaults

  $_filename = $filename ? { "" => "id_${keytype}", default => $filename }

  $_length = $keytype ? { "rsa" => $length, "dsa" => 1024, }               

  $_user = $user ? {                                                      

    ""      => regsubst($title, '^([^@]*)@?.*$', '\1'),                   

    default => $user,                                                     

  }                                                                       

  $_home = $home ? { "" => "/home/$_user",  default => $home }            



  ssh_auth_key_namecheck { "${title}-filename": parm => "filename", value => $_filename }



  @ssh_auth_key_master { $title:

    ensure  => $ensure,         

    force   => $force,          

    keytype => $keytype,        

    length  => $_length,        

    maxdays => $maxdays,        

    mindate => $mindate,        

  }                             

  @ssh_auth_key_client { $title:

    ensure   => $ensure,        

    filename => $_filename,     

    group    => $group,         

    home     => $_home,         

    user     => $_user,         

  }                             

  @ssh_auth_key_server { $title:

    ensure  => $ensure,         

    group   => $group,          

    home    => $_home,          

    options => $options,        

    user    => $_user,          

  }                             

}                               





##########################################################################





# ssh::auth::keymaster

#                     

# Keymaster host:     

# Create key storage; create, regenerate, and remove key pairs



class keymaster {



  # Set up key storage



  file { $ssh::auth::keymaster_storage:
    path   => '/var/lib/keys',
    ensure => directory,               
    owner  => puppet,                  
    group  => puppet,                  
    mode   => 644,                     
  }                                    

                                       

  # Realize all virtual master keys    

  Ssh_auth_key_master <| |>            



} # class keymaster





##########################################################################





# ssh::auth::client

#                  

# Install generated key pairs onto clients



define client ($ensure = "", $filename = "", $group = "", $home = "", $user = "") {



  # Realize the virtual client keys.

  # Override the defaults set in ssh::auth::key, as needed.

  if $ensure   { Ssh_auth_key_client <| title == $title |> { ensure   => $ensure   } }

  if $filename { Ssh_auth_key_client <| title == $title |> { filename => $filename } }

  if $group    { Ssh_auth_key_client <| title == $title |> { group    => $group    } }



  if $user { Ssh_auth_key_client <| title == $title |> { user => $user, home => "/home/$user" } }

  if $home { Ssh_auth_key_client <| title == $title |> { home => $home } }                       



  realize Ssh_auth_key_client[$title]



} # define client





##########################################################################





# ssh::auth::server

#                  

# Install public keys onto clients



define server ($ensure = "", $group = "", $home = "", $options = "", $user = "") {



  # Realize the virtual server keys.

  # Override the defaults set in ssh::auth::key, as needed.

  if $ensure  { Ssh_auth_key_server <| title == $title |> { ensure  => $ensure  } }

  if $group   { Ssh_auth_key_server <| title == $title |> { group   => $group   } }

  if $options { Ssh_auth_key_server <| title == $title |> { options => $options } }



  if $user { Ssh_auth_key_server <| title == $title |> { user => $user, home => "/home/$user" } }

  if $home { Ssh_auth_key_server <| title == $title |> { home => $home } }                       



  realize Ssh_auth_key_server[$title]



} # define server



} # class ssh::auth





##########################################################################





# ssh_auth_key_master

#                    

# Create/regenerate/remove a key pair on the keymaster.

# This definition is private, i.e. it is not intended to be called directly by users.

# ssh::auth::key calls it to create virtual keys, which are realized in ssh::auth::keymaster.



define ssh_auth_key_master ($ensure, $force, $keytype, $length, $maxdays, $mindate) {



  Exec { path => "/usr/bin:/usr/sbin:/bin:/sbin" }

  File {                                          

    owner => puppet,                              

    group => puppet,                              

    mode  => 600,                                 

  }                                               



  $keydir = "${ssh::auth::keymaster_storage}/${title}"

  $keyfile = "${keydir}/key"                          



  file { 

    "$keydir":

      ensure => directory,

      mode   => 644;      

    "$keyfile":           

      ensure => $ensure;  

    "${keyfile}.pub":     

      ensure => $ensure,  

      mode   => 644;      

  }                       



  if $ensure == "present" {



    # Remove the existing key pair, if

    # * $force is true, or            

    # * $maxdays or $mindate criteria aren't met, or

    # * $keytype or $length have changed            



    $keycontent = file("${keyfile}.pub", "/dev/null")

    if $keycontent {                                 



      if $force {

        $reason = "force=true"

      }                       

      if !$reason and $mindate and generate("/usr/bin/find", $keyfile, "!", "-newermt", "${mindate}") {

        $reason = "created before ${mindate}"                                                          

      }                                                                                                

      if !$reason and $maxdays and generate("/usr/bin/find", $keyfile, "-mtime", "+${maxdays}") {      

        $reason = "older than ${maxdays} days"                                                         

      }                                                                                                

      if !$reason and $keycontent =~ /^ssh-... [^ ]+ (...) (\d+)$/ {                                   

        if       $keytype != $1 { $reason = "keytype changed: $1 -> $keytype" }                        

        else { if $length != $2 { $reason = "length changed: $2 -> $length" } }                        

      }                                                                                                

      if $reason {                                                                                     

        exec { "Revoke previous key ${title}: ${reason}":                                              

          command => "rm $keyfile ${keyfile}.pub",                                                     

          before  => Exec["Create key $title: $keytype, $length bits"],                                

        }                                                                                              

      }                                                                                                

    }                                                                                                  



    # Create the key pair.

    # We "repurpose" the comment field in public keys on the keymaster to

    # store data about the key, i.e. $keytype and $length.  This avoids  

    # having to rerun ssh-keygen -l on every key at every run to determine

    # the key length.                                                     

    exec { "Create key $title: $keytype, $length bits":                   

      command => "ssh-keygen -t ${keytype} -b ${length} -f ${keyfile} -C \"${keytype} ${length}\" -N \"\"",

      user    => "puppet",                                                                                 

      group   => "puppet",                                                                                 

      creates => $keyfile,                                                                                 

      require => File[$keydir],                                                                            

      before  => File[$keyfile, "${keyfile}.pub"],                                                         

    }                                                                                                      



  } # if $ensure  == "present"



} # define ssh_auth_key_master





##########################################################################





# ssh_auth_key_client

#                    

# Install a key pair into a user's account.

# This definition is private, i.e. it is not intended to be called directly by users.



define ssh_auth_key_client ($ensure, $filename, $group, $home, $user) {



  File {

    owner   => $user,

    group   => $group,

    mode    => 600,   

    require => [ User[$user], ],

  }                                                    



  $key_src_file = "${ssh::auth::keymaster_storage}/${title}/key" # on the keymaster

  $key_tgt_file = "${home}/.ssh/${filename}" # on the client                       



  $key_src_content_pub = file("${key_src_file}.pub", "/dev/null")

  if $ensure == "absent" or $key_src_content_pub =~ /^(ssh-...) ([^ ]+)/ {

    $keytype = $1                                                         

    $modulus = $2                                                         

    file {                                                                

      $key_tgt_file:                                                      

        ensure  => $ensure,                                               

        content => file($key_src_file, "/dev/null");                      

      "${key_tgt_file}.pub":                                              

        ensure  => $ensure,                                               

        content => "$keytype $modulus $title\n",                          

        mode    => 644;                                                   

    }                                                                     

  } else {                                                                

    notify { "Private key file $key_src_file for key $title not found on keymaster; skipping ensure => present": }

  }                                                                                                               



} # define ssh_auth_key_client





##########################################################################





# ssh_auth_key_server

#                    

# Install a public key into a server user's authorized_keys(5) file.

# This definition is private, i.e. it is not intended to be called directly by users.



define ssh_auth_key_server ($ensure, $group, $home, $options, $user) {



  # on the keymaster:

  $key_src_dir = "${ssh::auth::keymaster_storage}/${title}"

  $key_src_file = "${key_src_dir}/key.pub"                 

  # on the server:                                         

  $key_tgt_file = "${home}/.ssh/authorized_keys"           

                                                           

  File {                                                   

    owner   => $user,                                      

    group   => $group,                                     

    require => User[$user],                                

    mode    => 600,                                        

  }                                                        

  Ssh_authorized_key {                                     

    user   => $user,                                       

    target => $key_tgt_file,                               

  }                                                        



  if $ensure == "absent" {

    ssh_authorized_key { $title: ensure => "absent" }

  }                                                  

  else {

    $key_src_content = file($key_src_file, "/dev/null")

    if ! $key_src_content {

      notify { "Public key file $key_src_file for key $title not found on keymaster; skipping ensure => present": }

    } else { if $ensure == "present" and $key_src_content !~ /^(ssh-...) ([^ ]*)/ {

      err("Can't parse public key file $key_src_file")

      notify { "Can't parse public key file $key_src_file for key $title on the keymaster: skipping ensure => $ensure": }

    } else {

      $keytype = $1

      $modulus = $2

      ssh_authorized_key { $title:

        ensure  => "present",

        type    => $keytype,

        key     => $modulus,

        options => $options ? { "" => undef, default => $options },

      }

    }} # if ... else ... else

  } # if ... else



} # define ssh_auth_key_server





##########################################################################





# ssh_auth_key_namecheck

#

# Check a name (e.g. key title or filename) for the allowed form



define ssh_auth_key_namecheck ($parm, $value) {

  if $value !~ /^[A-Za-z0-9]/ {

    fail("ssh::auth::key: $parm '$value' not allowed: must begin with a letter or digit")

  }

  if $value !~ /^[A-Za-z0-9_.:@-]+$/ {

    fail("ssh::auth::key: $parm '$value' not allowed: may only contain the characters A-Za-z0-9_.:@-")

  }

} # define namecheck
