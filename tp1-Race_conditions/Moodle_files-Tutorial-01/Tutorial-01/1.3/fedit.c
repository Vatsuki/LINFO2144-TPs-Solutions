#include "stdlib.h"
#include "stdio.h"
#include "unistd.h"
#include "fcntl.h"

int main(int argc, char *argv[]) {
  int fd;
  char *v[2];
  if (argc > 2) { printf("Insufficient arguments, usage %s <filename>\n", argv[0]); return 1; } 
  fd = open(argv[1],O_RDWR | O_APPEND);
  if (fd==-1){
    printf("cannot open file %s\n", argv[1]);
    exit(0);
  }
  printf("fd is %d\n", fd);
  setuid(getuid());
  v[0] = "/bin/sh"; v[1] = 0;
  execve(v[0],v,0);
  return 0;
}

