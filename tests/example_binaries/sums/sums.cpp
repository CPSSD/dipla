#include <iostream>
#include <stdlib.h>


using namespace std;

int main(int argc, char *argv[]) {
  
  if (argc < 2) {
    cout << "Not enough arguments" << endl;
    return 1;
  }

  string arg = argv[1];

  // This code's purpose is to parse out the JSON provided on argv
  int end_of_num_A = arg.find(",");
  int numA = atoi(arg.substr(1, end_of_num_A - 1).c_str());
  int numB = atoi(arg.substr(
    end_of_num_A + 2,
    arg.size() - end_of_num_A - 3).c_str());

  int sum = numA + numB;

  string output = "{\"data\": , \"signals\": {}}";
  output.insert(9, to_string(sum));
  cout << output << endl;

  return 0;
}

