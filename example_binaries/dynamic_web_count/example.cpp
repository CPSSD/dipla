// This program takes a string from the arguments and counts the occurences of
// the string in each of the URLs provided by stdin. To quit the program enter
// a URL of '!'.

#include <iostream>
#include <curl/curl.h>

// A callback to append data onto a databuffer (string).
size_t write_callback(char* contents, size_t size,
                      size_t nmemb, std::string *databuff) {
  databuff->append(contents, size * nmemb);
  return size * nmemb;
}

// Count the occurences of the second string inside the first.
int count_substr(const std::string& base, const std::string& sub) {
  int count = 0;
  size_t pos = base.find(sub, 0);
  while(pos != std::string::npos) {
    ++count;
    pos = base.find(sub, pos + 1);
  }
  return count;
}

int main(int argc, char* argv[]) {
  if (argc < 2) {
    std::cout << "Please provide a string to match with";
    return 1;
  }

  // Set up cURL.
  CURL *curl = curl_easy_init();
  CURLcode res;
  std::string response;
  curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);  

  // Run in a loop, reading in new URLs from stdin.
  std::string url;
  std::cin >> url;
  while(url != "!") {
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    res = curl_easy_perform(curl);
    // If the request errors then print -1, otherwise count substrings.
    if(res != CURLE_OK) {
      std::cout << "-1";
    } else {
      std::cout << count_substr(response, argv[1]) << std::endl;
    }
    // Reset response and get a new URL 
    response = "";
    std::cin >> url;
  }
  curl_easy_cleanup(curl);
  return 0;
}
