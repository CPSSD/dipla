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
  
  if (argc < 3) {
    cout << "Usage: web_count <url> <search_term>" << endl;
    return 1;
  }

  CURL *curl = curl_easy_init();
  CURLcode res;
  string response;
  curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);  

  curl_easy_setopt(curl, CURLOPT_URL, argv[1]);
  res = curl_easy_perform(curl);
  if(res != CURLE_OK) {
    cout << "-1";
  } else {
    cout << count_substr(response, argv[2]) << endl;
  }
  
  curl_easy_cleanup(curl);
  return 0;
}
