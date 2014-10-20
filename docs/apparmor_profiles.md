#Generating apparmor profiles for tor and apache

```
vagrant up /staging$/
vagrant ssh app-staging
sudo su
cd /var/www/securedrop
```

(run tests, use the application, restart service, power off power on)

`aa-logprof`

(follow prompts and save at the end)

`aa-complain /etc/apparmor.d/PROFILE_NAME`

(run tests, use the application, restart service, power off power on)

`aa-logprof`

Repeat.

The apparmor profiles are saved in `/etc/apparmor.d/`
There are two profiles:
 - usr.sbin.tor
 - usr.sbin.apache2

After running `aa-logprof` you will need to copy the modified profile back to your host machine.

cp /etc/apparmor.d/usr.sbin.apache2 /vagrant/install_files/ansible-base
cp /etc/apparmor.d/usr.sbin.tor /vagrant/install_files/ansible-base

The apparmor profiles are packaged with the securedrop-app-code.
The securedrop-app-code postinst puts the apparmor profiles in enforce mode.
The `app-test` ansible module (which is run as part of staging but not prod) puts the apparmor profiles in enforce mode.
