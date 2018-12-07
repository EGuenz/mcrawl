Main generates min(n,8) new_user threads and main() waits for these threads to exit. Each new_user thread initiates a new connection to the server and retrieves a cookie. A shared queue q containing local files to crawl is passed to each thread. Each thread calls crawl(), which
1) Retrieves filename by calling queue.get()
2) creates a GET request to server for file
3) downloads file flat to folder specified
4) Finds all local links in that file if it is a text file and puts new links to queue.
5) calls crawl() again with cookie

If queue is empty for 2 seconds crawl() returns and thread exits.

Delete download folder after use for correct behavior
