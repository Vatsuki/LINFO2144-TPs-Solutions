#include <stdio.h>
#include <pthread.h>

void *f(void *v) {       
  int *i = (int *) v;        
  *i = 0;        
  printf("set to 0!\n");        
  return NULL;
}

int main() {	
  const int c = 1;	 int i = 0;	pthread_t thread;	
  void *ptr =(void *) &c;	
  while(c) {			
    i++;		
    if (i == 1000) {			
      pthread_create(&thread, NULL, &f, ptr);
    }
  }	
  printf("done\n");
}

