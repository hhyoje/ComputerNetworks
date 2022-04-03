#proxy.py

import os
import sys
import socket
import struct
import _thread
import time

def parse_headers(msg):
    # Cut off body, split up headers, remove first line, and add the headers to a dictionary
    d = {}
    msg = msg.split('\r\n\r\n')[0]
    headers = msg.split('\r\n')	
    headers.pop(0);	
    for header in headers:
        h = header.split(': ', 1)
        d[h[0]] = h[1]  
    return d

def parse_message(msg, split_by, default):
    # Split msg into two parts, if second part doesn't exist, assign default
    m = msg.split(split_by, 1)
    x = m[0]
    if(len(x) == 1):
        y = default
    else:
        y = m[1]
    return x, y

def recv_all(conn, wait_time = 3):
    # Keep receiving data in a loop until it times out and breaks
    conn.setblocking(0)
    msg = '';
    t = time.time()
    while True:
        if time.time() - t > wait_time:
            break
        try: 
            data = conn.recv(2048)
            if data:
                msg += data.decode()
                t = time.time()
        except:
            pass
    return msg

def proxy_client(host, port, client_request, body):
    # Client side does socket and connect, generates request based on request received on server side, sends the generated request, and receives data
    s = socket.socket()
    s.connect((host, int(port)))
    age = int(time.time())

    # If cache file exists
    if(os.path.isfile('cache')):
        f = open('cache', 'r')
        response = f.read()
        f.close()
        # If same URL
        if( (client_request.split(' ', 1)[1]).split('\r\n', 2)[:2] == (response.split(' ', 1)[1]).split('\r\n', 2)[:2]):
            d = parse_headers(response)
            # If age is less than max-age
            if(age < d['Cache-control'].split('max-age=', 1)[1]):
                # Instead of sending request to server, send contents in cache file
                return response

    # Formulate request with added headers, send the request, and receive the response
    request = client_request + '\r\nX-4119: dsl2167 ' + str(age) + '\r\nX-Forwarded-For: ' + socket.gethostbyname(socket.gethostname()) + '\r\n\r\n' + body
    s.sendall(request.encode())
    response = recv_all(s)

    # If 200 OK response
    if(response.split('\r\n', 1)[0].split(' ', 1)[1] == '200 OK'):
        # Create cache file with response
        f = open('cache', 'w+')
        f.write(response)
        f.close()

    return response

def proxy_server():
    host = ''
    port = int(sys.argv[1])

    # Server does socket, bind, listen
    s = socket.socket()
    s.bind((host, port))
    s.listen(10)
    print('Socket is listening..')

    # Server function for threads (multiple clients)
    def client_thread(conn):
        # Receive request from client and make dictionary from request headers
        request = recv_all(conn)
        d = parse_headers(request)
        
        # If 'Host' header is found, send request to server
        if('Host' in d):
            # Parse 'Host' header for host and port, parse entire client message for request line + headers and body
            host_name, port_number = parse_message(d['Host'], ':', '80')
            print('Sending request to ' + host_name + ' on port ' + port_number)
            client_request, body = parse_message(request, '\r\n\r\n', '')
	    # Host, port, request, and body from client request is used on proxy client side, returning a response from the server
            response = proxy_client(host_name, port_number, client_request, body)
            # Send response back to client with proxy server side
            conn.sendall(response.encode())
        
        # If 'Host' header is not found, do not send request and notify
        else:
            print('Error: No host found in request')
        conn.close()

    # Continue accepting client connections and create a new thread each time
    while True:
        _thread.start_new_thread(client_thread, (s.accept()[0], ))

    s.close()


proxy_server()
