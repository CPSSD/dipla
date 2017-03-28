/*
 * This is a modified version of CianLR's dynamic_web_count.
 *
 * It uses argv instead of stdin to get input.
 *
 */

#include <iostream>
#include <curl/curl.h>

using namespace std;

size_t write_callback(char* contents, size_t size,
                      size_t nmemb, string *databuff) {
  databuff->append(contents, size * nmemb);
  return size * nmemb;
}

int count_substr(const string& base, const string& sub) {
  int count = 0;
  size_t pos = base.find(sub, 0);
  while(pos != string::npos) {
    ++count;
    pos = base.find(sub, pos + 1);
  }
  return count;
}

int main(int argc, char* argv[]) {
  
  if (argc < 2) {
    cout << "Usage: web_count [<url>, <search_term>]" << endl;
    return 1;
  }

  string arg = argv[1];

  // This code's purpose is to parse out the JSON provided on argv
  int end_of_url = arg.find("\",");
  string url = arg.substr(2, end_of_url - 2);
  string term = arg.substr(
    end_of_url + 4,
    arg.size() - end_of_url - 6);

  CURL *curl = curl_easy_init();
  CURLcode res;
  string response;
  curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);  

  curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
  res = curl_easy_perform(curl);
  int num_substr = -1;
  if(res == CURLE_OK) {
    num_substr = count_substr(response, term);
  }

  string output = "{\"data\": }";
  output.insert(9, to_string(num_substr));
  cout << output << endl;

  curl_easy_cleanup(curl);
  return 0;
}
