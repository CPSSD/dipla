# Web Count

This is a modified version of CianLR's original example binary.

## Compilation

This binary is writen in C++ and requires the libcurl library, specifically `libcurl4-gnutls-dev`

To compile run `g++ web_count.cpp -o web_count -lcurl`

You will then have a `web_count` executable.

## Usage

The program is run with two command-line arguments.

1. The url you want to fetch data from.
2. The substring you want to check for.

E.g. `./web_count http://www.test.com word`

This will count the number of times `word` shows up on `http://www.test.com`.

If `-1` has been printed, it indicates an error with your input.

