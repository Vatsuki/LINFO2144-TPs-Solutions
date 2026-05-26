#include "stdlib.h"
#include "stdio.h"
#include "string.h"

int main(int argc, char *argv[]) {
  if (argc != 2) { printf("Usage: \"%s n\" to delay for n seconds\n",argv[0]); return 1;}
  char *sleep ="/bin/sleep";
  char *command = malloc(strlen(sleep) + strlen(argv[1]) +2);
  sprintf(command, "%s %s", sleep, argv[1]);
  system(command);
  return 0;
}

