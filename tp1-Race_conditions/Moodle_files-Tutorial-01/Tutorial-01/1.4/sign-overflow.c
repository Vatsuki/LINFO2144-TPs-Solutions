#include "stdio.h"

int main() {
  short nb1, nb2, 
  res = 0; printf("enter first digit : "); 
  scanf("%hd", &nb1); 
  printf("enter second digit : "); 
  scanf("%hd", &nb2);

  res = nb1 + nb2; 
  printf("%hd + %hd = %hd\n", nb1, nb2, res);
 
  return 0;
} 

