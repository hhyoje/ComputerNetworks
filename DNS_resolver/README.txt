DNS Resolver
dsl2167

This program is ran by entering 'python3 main.py <port>', where
<port> is the port number that will be used for the server.
To use this server, you enter 'dig -p <port> <domain> @127.0.0.1 
as a client, where <port> is the same port number used for the 
server and <domain> is the domain you are trying to get an answer 
from. 

When the server starts, an empty cache is created and server() is 
called. The server the standard sockets operations and repeatedly
listens for requests. When a request is received, client(query) is
called to resolve the request.

The client() operation also does the standard sockets operations 
for sending UDP requests, sets the recursion bit to 0, and parses 
the domain into separate parts. Then, while an answer is not found, 
either a cached response is returned if available, or a query is sent
to the next server. When sending a query, the returned response is 
cached. The socket is closed and finally, the response containing an 
answer is returned to the server, which sends the response back to 
the client that made the intial request.
