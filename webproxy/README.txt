Web Proxy
dsl2167

This program is run by entering 'python3 proxy.py <port-number>'
where <port-number> is the port number you use for server side of the proxy.

The server side of the proxy was implemented first in proxy_server().
The server does the standard sockets operation and then accepts clients 
on loop, creating a new thread each time. Each thread receives the client
request, organizes headers into a dictionary, and sends/receives with the
server the client was trying to communicate with. Three functions were 
created to assist with this part: parse_headers(), parse_message(), and
recv_all(). If no 'Host' header is in the dictionary, the operation ends 
and there is no client side operation.

parse_headers() organizes the headers with string manipulation.
parse_message() rearranges information to a more useful form.
recv_all() repeatedly calls recv() on loop until it times out 
when too much time passes on a call, at which point the loop ends.

The client side was implemented next in proxy_client(). It receives
relevant information from the server side to make a proper request
(or use the cache). This information includes the host and port of
the server, the request line, headers, and the body (if there is one)
of the request. parse_message is used to separate the request line and 
headers from the body so that more headers can be added. At this point,
the client side must decide whether to send back cached data or send
the request to the server. This decision comes down to a series of
conditionals (specified in code comments), and if they all evaluate
to true, the cached data is sent back and the client function returns.
Otherwise, a request is sent. At this point, the client must decide
whether to cache this response, which is based on if it is a 200 OK
response. The client side then returns the response to the server 
side. The server, with no knowledge of if it receieved a cached
or "real" response, sends the encoded response back to the original
client and the connection ends there.

The screenshots of operation are in the written homework submission.
