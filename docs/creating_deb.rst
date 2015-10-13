Creating the deb packages for SecureDrop
========================================

Gathering OSSEC files
---------------------

| OSSEC can be downloaded from their website or cloned from git.
| https://www.ossec.net

The installed files are different for both the agent and server.

Install the OSSEC server
~~~~~~~~~~~~~~~~~~~~~~~~

::

    root@dmon:~/ossec-hids# ls
    active-response  CONFIG   CONTRIBUTORS  etc      install.sh  README.md
    BUGS             contrib  doc           INSTALL  LICENSE     src
    root@dmon:~/ossec-hids# ./install.sh

      ** Para instala????o em portugu??s, escolha [br].
      ** ???????????????????????????, ????????? [cn].
      ** Fur eine deutsche Installation wohlen Sie [de].
      ** ?????? ?????????????????????? ?????? ????????????????, ???????????????? [el].
      ** For installation in English, choose [en].
      ** Para instalar en Espa??ol , eliga [es].
      ** Pour une installation en fran??ais, choisissez [fr]
      ** A Magyar nyelv?? telep??t??shez v??lassza [hu].
      ** Per l'installazione in Italiano, scegli [it].
      ** ???????????????????????????????????????????????????????????????jp].
      ** Voor installatie in het Nederlands, kies [nl].
      ** Aby instalowa?? w j??zyku Polskim, wybierz [pl].
      ** ????????????????????????? ???? ?????????????????? ???? ?????????????? ,?????????????? [ru].
      ** Za instalaciju na srpskom, izaberi [sr].
      ** T??rk??e kurulum i??in se??in [tr].
      (en/br/cn/de/el/es/fr/hu/it/jp/nl/pl/ru/sr/tr) [en]:


     OSSEC HIDS v2.8 Installation Script - http://www.ossec.net

     You are about to start the installation process of the OSSEC HIDS.
     You must have a C compiler pre-installed in your system.
     If you have any questions or comments, please send an e-mail
     to dcid@ossec.net (or daniel.cid@gmail.com).

      - System: Linux dmon 3.13.0-32-generic
      - User: root
      - Host: dmon


      -- Press ENTER to continue or Ctrl-C to abort. --


    1- What kind of installation do you want (server, agent, local, hybrid or help)? server

      - Server installation chosen.

    2- Setting up the installation environment.

     - Choose where to install the OSSEC HIDS [/var/ossec]:

        - Installation will be made at  /var/ossec .

    3- Configuring the OSSEC HIDS.

      3.1- Do you want e-mail notification? (y/n) [y]:
       - What's your e-mail address? securedrop@freedom.press

       - We found your SMTP server as: smtp.electricembers.net.
       - Do you want to use it? (y/n) [y]: y

       --- Using SMTP server:  smtp.electricembers.net.

      3.2- Do you want to run the integrity check daemon? (y/n) [y]: y

       - Running syscheck (integrity check daemon).

      3.3- Do you want to run the rootkit detection engine? (y/n) [y]: y

       - Running rootcheck (rootkit detection).

      3.4- Active response allows you to execute a specific
           command based on the events received. For example,
           you can block an IP address or disable access for
           a specific user.
           More information at:
           http://www.ossec.net/en/manual.html#active-response

       - Do you want to enable active response? (y/n) [y]: n

         - Active response disabled.

      3.5- Do you want to enable remote syslog (port 514 udp)? (y/n) [y]: n

       --- Remote syslog disabled.

      3.6- Setting the configuration to analyze the following logs:
        -- /var/log/auth.log
        -- /var/log/syslog
        -- /var/log/dpkg.log

     - If you want to monitor any other file, just change
       the ossec.conf and add a new localfile entry.
       Any questions about the configuration can be answered
       by visiting us online at http://www.ossec.net .


       --- Press ENTER to continue ---

Create the zipped files for the OSSEC server files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    root@dmon:~/ossec-hids# mkdir ../monitor-ossec
    root@dmon:~/ossec-hids# mkdir ../monitor-ossec/etc
    root@dmon:~/ossec-hids# cp /etc/ossec-init.conf ../monitor-ossec/etc/
    root@dmon:~/ossec-hids# mkdir ../monitor-ossec/var/
    root@dmon:~/ossec-hids# cp -R /var/ossec/ ../monitor-ossec/var/
    root@dmon:~/ossec-hids# mkdir ../monitor-ossec/etc/init.d
    root@dmon:~/ossec-hids# cp /etc/init.d/ossec ../monitor-ossec/etc/init.d/
    root@dmon:~/ossec-hids# rm ../monitor-ossec/var/ossec/etc/ossec.conf

Install OSSEC agent
~~~~~~~~~~~~~~~~~~~

::

    root@dapp:~/ossec-hids# ./install.sh

      ** Para instala????o em portugu??s, escolha [br].
      ** ???????????????????????????, ????????? [cn].
      ** Fur eine deutsche Installation wohlen Sie [de].
      ** ?????? ?????????????????????? ?????? ????????????????, ???????????????? [el].
      ** For installation in English, choose [en].
      ** Para instalar en Espa??ol , eliga [es].
      ** Pour une installation en fran??ais, choisissez [fr]
      ** A Magyar nyelv?? telep??t??shez v??lassza [hu].
      ** Per l'installazione in Italiano, scegli [it].
      ** ???????????????????????????????????????????????????????????????jp].
      ** Voor installatie in het Nederlands, kies [nl].
      ** Aby instalowa?? w j??zyku Polskim, wybierz [pl].
      ** ????????????????????????? ???? ?????????????????? ???? ?????????????? ,?????????????? [ru].
      ** Za instalaciju na srpskom, izaberi [sr].
      ** T??rk??e kurulum i??in se??in [tr].
      (en/br/cn/de/el/es/fr/hu/it/jp/nl/pl/ru/sr/tr) [en]:


     OSSEC HIDS v2.8 Installation Script - http://www.ossec.net

     You are about to start the installation process of the OSSEC HIDS.
     You must have a C compiler pre-installed in your system.
     If you have any questions or comments, please send an e-mail
     to dcid@ossec.net (or daniel.cid@gmail.com).

      - System: Linux dmon 3.13.0-32-generic
      - User: root
      - Host: dmon


      -- Press ENTER to continue or Ctrl-C to abort. --


    1- What kind of installation do you want (server, agent, local, hybrid or help)? agent

      - Agent(client) installation chosen.

    2- Setting up the installation environment.

     - Choose where to install the OSSEC HIDS [/var/ossec]:

        - Installation will be made at  /var/ossec .

    3- Configuring the OSSEC HIDS.

      3.1- What's the IP Address or hostname of the OSSEC HIDS server?: 192.168.2.2

       - Adding Server IP 192.168.2.2

      3.2- Do you want to run the integrity check daemon? (y/n) [y]:

       - Running syscheck (integrity check daemon).

      3.3- Do you want to run the rootkit detection engine? (y/n) [y]:

       - Running rootcheck (rootkit detection).

      3.4 - Do you want to enable active response? (y/n) [y]: n

       - Active response disabled.

      3.5- Setting the configuration to analyze the following logs:
        -- /var/log/auth.log
        -- /var/log/syslog
        -- /var/log/dpkg.log

     - If you want to monitor any other file, just change
       the ossec.conf and add a new localfile entry.
       Any questions about the configuration can be answered
       by visiting us online at http://www.ossec.net .


       --- Press ENTER to continue ---

Create the zipped files for the OSSEC agent files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    root@dapp:~/ossec-hids# mkdir ../ossec-agent
    root@dapp:~/ossec-hids# mkdir -p ../ossec-agent/etc/init.d
    root@dapp:~/ossec-hids# mkdir -p ../ossec-agent/var
    root@dapp:~/ossec-hids# cp -R /var/ossec/ ../ossec-agent/var/
    root@dapp:~/ossec-hids# cp /etc/ossec-init.conf ../ossec-agent/etc/
    root@dapp:~/ossec-hids# cp /etc/init.d/ossec ../ossec-agent/etc/init.d/
    strip ../ossec-agent/var/ossec/bin/*
