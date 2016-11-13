#include <iostream>
#include <stdlib.h>


using namespace std;

int main(int argc, char *argv[]) {
  
  if (argc < 3) {
    cout << "Not enough arguments" << endl;
    return 1;
  }

  int numA = atoi(argv[1]);
  int numB = atoi(argv[2]);
  int sum = numA + numB;

  cout << sum << endl;

  return 0;
}

