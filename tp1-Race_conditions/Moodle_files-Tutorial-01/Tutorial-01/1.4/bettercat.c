#include "stdlib.h"
#include "stdio.h"
#include "string.h"

int main(int argc, char *argv[]){
  unsigned int s = 1024; 
  int i; 
  char *buf;
  if (argc > 2) {
    i = atoi(argv[2]); 
    if (i>1024){ printf("Buffer size too large\n"); return 1;}
    s = i;
  }
  buf = malloc(s);
  FILE *file;
  int nread;
  file = fopen(argv[1],"r");
  if (file) {
    while ((nread = fread(buf, 1, s, file)) > 0) {
      if (nread < s) { buf[nread] = 0; }
      printf("%s",buf);
    }
    fclose(file);
  }
  free(buf);
  return 0;
} 

