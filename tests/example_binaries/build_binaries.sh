#!/bin/bash

BIN_DIR="tests/example_binaries"

echo "Downloading C/C++ dependencies (if necessary)..."
sudo apt-get install libcurl4-gnutls-dev

echo "About to build binaries..."

g++ -o $BIN_DIR/dynamic_web_count/example.exe $BIN_DIR/dynamic_web_count/example.cpp -lcurl -std=c++11

g++ -o $BIN_DIR/web_count/web_count.exe $BIN_DIR/web_count/web_count.cpp -lcurl -std=c++11

g++ -o $BIN_DIR/sums/sums.exe $BIN_DIR/sums/sums.cpp -std=c++11

echo "Done."

