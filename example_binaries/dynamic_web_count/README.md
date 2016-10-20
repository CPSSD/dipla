# Example Binary

## Compilation

This binary is writen in C++ and requires the libcurl library, specifically `libcurl4-gnutls-dev`

To compile run `g++ example.cpp -o example -lcurl`

You will then have an `example` executable.

## Usage

The program is run with one command-line argument, the substring to search for.

E.g. `./example dcu` will search for the (case sensitive) string `dcu` at the provided URLs.

URLs are provided to the program on stdin, for each line on stdin a line on stdout will be
printed with an integer reperesenting the number of occurences of the substring or a `-1`
indicating an error.

Entering `!` or hitting Ctrl-C at any point will quit.

