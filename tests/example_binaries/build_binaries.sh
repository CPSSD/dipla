

echo "Downloading C/C++ dependencies (if necessary)..."
sudo apt-get install libcurl4-gnutls-dev

echo "About to build binaries..."

g++ -o dynamic_web_count/example.exe dynamic_web_count/example.cpp -lcurl

g++ -o web_count/web_count.exe web_count/web_count.cpp -lcurl

g++ -o sums/sums.exe sums/sums.cpp

echo "Done."

