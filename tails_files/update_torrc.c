/* This program adds everything in torrc.additions to the end of /etc/tor/torrc 
 * and reloads the tor service. This way you can add customizations (such as 
 * HidServAuth lines) to the end of your torrc in Tails. 
 *
 * It requires the file: /home/amnesia/Persistent/torrc.additions
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char* argv) {
    // check for root
    if(geteuid() != 0) {
        printf("You need to run this as root\n");
        return 0;
    }

    char torrc[20480];
    char torrc_additions[4096];
    FILE *fp;

    // read torrc.additions
    fp = fopen("/home/amnesia/Persistent/torrc.additions", "r");
    if(!fp) {
        printf("Error opening /home/amnesia/Persistent/torrc.additions for reading\n");
        return 0;
    }
    fread(torrc_additions, sizeof(char), sizeof(torrc_additions), fp);
    fclose(fp);

    // load the original torrc
    if(access("/etc/tor/torrc.bak", F_OK) != -1) {
        fp = fopen("/etc/tor/torrc.bak", "r");
        fread(torrc, sizeof(char), sizeof(torrc), fp);
        fclose(fp);
    } else {
        fp = fopen("/etc/tor/torrc", "r");
        fread(torrc, sizeof(char), sizeof(torrc), fp);
        fclose(fp);

        fp = fopen("/etc/tor/torrc.bak", "w");
        fwrite(torrc, sizeof(char), strlen(torrc), fp);
        fclose(fp);
    }

    // append the additions
    fp = fopen("/etc/tor/torrc", "w");
    if(!fp) {
        printf("Error opening /etc/tor/torrc for writing\n");
        return 0;
    }
    fputs(torrc, fp);
    fputs(torrc_additions, fp);
    fclose(fp);

    // reload tor service
    setuid(0);
    system("/usr/sbin/service tor reload");
    system("/usr/bin/sudo -u amnesia /usr/bin/notify-send 'Updated torrc' 'You can now connect to your authenticated Tor hidden services'");
}
