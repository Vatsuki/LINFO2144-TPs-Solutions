#include "stdlib.h"
#include "stdio.h"
#include "string.h"

int main(int argc, char *argv[]) {
  if (argc < 3) { printf("Insufficient arguments\n");return 1; }
  char *echo ="/bin/echo";
  char *command = malloc(strlen(echo) + strlen(argv[2]) +2);
  sprintf(command, "%s %s", echo, argv[2]);
  unsigned char i = 0;
  int limit = atoi(argv[1]);
  while (i < limit) {
    system(command);
    i++;
  }
  free(command);
  return 0;
}

