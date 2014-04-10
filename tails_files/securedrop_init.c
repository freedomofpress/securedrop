int main(int argc, char* argv) {
   setuid(0);
   system("/home/amnesia/Persistent/.securedrop/securedrop_init.py");
   return 0;
}
