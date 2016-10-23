# Architecture

This document explains the general flow of the Dipla system.

The goal of Dipla is to distribute some work across a number of clients that opt-in to a certain task. This is achieved in the following way:

1. A client knows the address of a server, and opens websocket connection to it.
2. The server sends the client a binary that contains the logic of the work that will need to be distributed.
3. The client receives the binary and saves it to disk. It then waits on further input from the server.
4. The server has some collection of inputs it needs to be executed by various clients. It chooses a piece of data to be operated on first, and chooses the most suitable client out of the pool of ready clients. If the pool is empty, it waits until a client joins the pool.
5. The server transmits this piece of data to the particular client. The client is now considered busy, so it is taken out of the pool of ready clients.
6. The client uses this data as input to the binary it was sent. It runs this binary in a new process with the data passed in on stdin. It waits for a result from stdout. When it receives the result, it transmits this to the server.
7. The server receives the output from the client. The client is now ready for more work.
8. This repeats until all of the inputs the server had have been run. The server closes the connections the clients, and the clients shut down.
