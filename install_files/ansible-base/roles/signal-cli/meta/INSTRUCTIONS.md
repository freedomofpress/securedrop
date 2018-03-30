You can now receive SecureDrop OSSEC alerts via Signal. There are four (4) variables that control the configuration of this functionality, which can be found in  or `install_files/ansible-base/group_vars/all/site-specific`. Note that because of the precedence of variables, variables in `install_files/ansible-base/securedrop-staging.yml` will override the ones in `site-specific`.

- `signal_notifications` (default set to `False`) must be set to `True` (e.g.: `signal_notifications: True`) to enable Signal notifications for the SecureDrop install.
- `The signal number which will be used to send alerts (e.g.: `signal_number: "+15555555"`)
- `signal_cli_copy_config`: which will specify if the config at install_files/ansible-base/+15555555 will be copied over to the server (defaults to `False`)
- `signal_destination_number`: The number which will receive the signal notifications (e.g.: `signal_destination_number: "+15555556666"`)

Note that if you are using a staging environment, postfix service is stopped. You must enable the postfix service (`sudo service postfix start`) to enable the procmail filtering which calls the send_encrypted_alarm.sh script.

If you would like to set up your SecureDrop instance to also send OSSEC alerts via Signal, here are the steps you must take:

1- Acquire a phone number (VoIP service, a SIM card from a phone provider and temporarily use it on your phone). Ensure that you remain in control of this number, as an attacker could re-register that number and intercept OSSEC messages coming from your server. Make sure you can receive SMS sent to this number in a timely fashion.
2- Set `signal_notifications: True`, and specify the values of `signal_number` and `signal_destination_number`
3- If you already have a Signal configuration for a number or if you are restoring from a backup, move it to the `securedrop/install_files/ansible-base/` folder, set `signal_cli_copy_config: True` and go to step 4.
4- Once all variables are set, run the install script (`securedrop-admin install`).
5- If you have copied your signal configuration (step 3), you should be already be receiving Signal messages and setup of Signal notifications is complete. If you haven't copied the configuration or if this a new install, please continue to the next step.
6- Once the install completes, run `securedrop-admin tailsconfig`.
7- `securedrop-admin signal_register` and follow instructions. Congratulations, you should now be receiving Signal notifications. You may use the OSSEC alert test to confirm the alerts are working.
8- `securedrop-admin signal_backup` and follow instructions to backup the configuration to the admin workstation.
