#include <unistd.h>

int main(int argc, char* argv) {
   setuid(0);
   // Use absolute path to the Python binary and execl to avoid $PATH or symlink trickery
   execl("/usr/bin/python2.7", "python2.7", "/home/vagrant/tails_files/test.py", (char*)NULL);
   return 0;
}
