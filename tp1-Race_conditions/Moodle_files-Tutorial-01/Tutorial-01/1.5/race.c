#include "fcntl.h"
#include "stdio.h"
#include "sys/stat.h"

/*race.c*/

int main() { 
  struct stat st; FILE* fd; 
  
  if(!stat("password.txt", &st)) { 
     printf("file already exists\n"); 
     return 0;
   } 
  fd = fopen("password.txt", "ax");
  chmod("password.txt", S_IREAD | S_IEXEC | S_IWRITE); 
  fputs("monsupermotdepasse", fd);
  fflush(fd);
  fclose(fd); 
  return 0;
}

