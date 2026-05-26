#include "stdlib.h"
#include "stdio.h"
#include "string.h"

int main(int argc, char *argv[]){
  short s = 100; 
  int i = 100; 
  char buf[100];
  if (argc > 2) {
    i = atoi(argv[2]); 
    s = i; 
    if (s>100){ printf("Buffer size too large\n"); return 1;}
  }
  FILE *file;
  int nread;
  file = fopen(argv[1],"r");
  if (file) {
    while ((nread = fread(buf, 1, i, file)) > 0) {
      if (nread <= i) { buf[nread] = 0; }
      printf("%s",buf);
    }
    fclose(file);
  }
  return 0;
} 

