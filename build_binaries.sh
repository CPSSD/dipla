BIN_DIR="tests/example_binaries"


echo "Downloading C/C++ dependencies (if necessary)..."
sudo apt-get install libcurl4-gnutls-dev

echo "About to build binaries..."

g++ -o $BIN_DIR/dynamic_web_count/example.exe $BIN_DIR/dynamic_web_count/example.cpp -lcurl

g++ -o $BIN_DIR/web_count/web_count.exe $BIN_DIR/web_count/web_count.cpp -lcurl

echo "Done."

