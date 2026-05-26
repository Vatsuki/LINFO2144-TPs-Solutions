#include "stdlib.h"
#include "stdio.h"
#include "string.h"

int main(int argc, char *argv[])
  {char *cat ="/bin/cat";
  char *command = malloc(strlen(cat) + strlen(argv[1]) +2);
  sprintf(command, "%s %s", cat, argv[1]);
  system(command);
  return 0;}

