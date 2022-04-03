#main.py

import socket
import sys
import struct
import time

def flag_parser(Flags):
	bits = bin(Flags)[2:].zfill(16)
	d = {
		'QR' : bits[0],
		'Opcode' : bits[1:5],
		'AA' : bits[5],
		'TC' : bits[6],
		'RD' : bits[7],
		'RA' : bits[8],
		'Z' : bits[9:12],
		'RCODE' : bits[12:16]
	}
	return d

def header_parser(data):
	header = data[0:12]
	ID, Flags, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT = struct.unpack('>HHHHHH', header)
	d = {
		'ID' : ID,
		'QDCOUNT' : QDCOUNT,
		'ANCOUNT' : ANCOUNT,
		'NSCOUNT' : NSCOUNT,
		'ARCOUNT' : ARCOUNT
	}
	return d, Flags, data[12:]

def check_point(byte):
	p = bin(byte)[2:].zfill(8)
	if(p[0:2] == '11'):
		return True
	return False

def name_parser(data, original):
	point = True
	NAME = ''

	#if pointer then parse through previous section
	if(check_point(data[0])):
		z = int(struct.unpack('>H', data[0:2])[0])
		a = bin(z)[2:].zfill(16)
		index = int(a[2:16], 2)
		return name_parser(original[index:], original)[0], data[2:]

	#read number then read that many characters
	length = int(data[0])
	data = data[1:]
	while(length != 0):
		NAME += data[0:length].decode()
		NAME += '.'
		data = data[length:]
		
		#check if pointer
		if(check_point(data[0])):
			z = int(struct.unpack('>H', data[0:2])[0])
			a = bin(z)[2:].zfill(16)
			index = int(a[2:16], 2)
			return NAME + name_parser(original[index:], original)[0], data[2:]
		#else check for length
		length = int(data[0])
		data = data[1:]

	return NAME, data

def question_parser(data, original):
	QNAME, data = name_parser(data, original)	
	QTYPE, QCLASS = struct.unpack('>HH', data[0:4])
	d = {
		'QNAME' : QNAME,
		'QTYPE' : QTYPE,
		'QCLASS' : QCLASS
	}
	return d, data[4:]
	
def rr_parser(data, original):
	NAME, data = name_parser(data, original)
	TYPE, CLASS, TTL, RDLENGTH = struct.unpack('>HHIH', data[0:10])
	data = data[10:]
	RDATA = data[0:int(RDLENGTH)]
	d = {
		'NAME' : NAME,
		'TYPE' : TYPE,
		'CLASS' : CLASS,
		'TTL' : TTL,
		'RDLENGTH' : RDLENGTH,
		'RDATA' : RDATA
	}
	return d, data[int(RDLENGTH):]

def data_parser(data):
	#parse header
	d, Flags, remaining = header_parser(data)
	#parse flags section of header and update dict
	d['Flags'] = flag_parser(Flags)
	#add questions to dict and update dict
	for i in range(d['QDCOUNT']):
		d_question, remaining = question_parser(remaining, data)
		d['question' + str(i)] = d_question
	#add answers to dict and update dict
	for i in range(d['ANCOUNT']):
		d_answer, remaining = rr_parser(remaining, data)
		d['answer' + str(i)] = d_answer
	#authority + additional
	for i in range(d['NSCOUNT']):
		d_authority, remaining = rr_parser(remaining, data)
		d_authority['RDATA'] = name_parser(d_authority['RDATA'], data)[0]
		d['authority' + str(i)] = d_authority
	for i in range(d['ARCOUNT']):
		d_additional, remaining = rr_parser(remaining, data)
		d['additional' + str(i)] = d_additional

	return d

def set_RD(data):
	#RD is last bit in this byte and should be set to 0
	data = data - data % 2
	return data.to_bytes(1, 'big')


def client(query):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	answered = False

	#set RD to 0 and parse query
	query = query[0:2] + set_RD(query[2]) + query[3:]
	d = data_parser(query)
	#DNS servers to query/cache
	iterate = -1
	dns = d['question0']['QNAME'].split('.')
	dns.pop()
	#root server
	address = 'l.root-servers.net'
	#need to log past entry to not be stuck in loop
	past_entry = ''
	past_address = ''
	#while answer is not found
	while(answered == False):
		resp = b''
		#if past entry is same, chnage current entry so that loop breaks
		entry = '.' + '.'.join(dns[iterate:])
		if(entry == past_entry):
			entry = '.' + entry
		past_entry = entry
		iterate -= 1
		#if address is cached
		cached = False
		if(entry in cache):
			#if the cache data has not expired
			if(int(time.time()) < int(cache[entry][1])):
				resp = query[0:2] + cache[entry][0][2:]
				address = cache[entry][2]
				#if answer
				if(cache[entry][3]):
					answered = True
				cached = True
			#if cache data expired, delete it
			else:
				cache.pop(entry)

		#if no available cache data, send query
		if(cached == False):
			#send query and get response
			s.sendto(query, (address, 53))
			resp, addr = s.recvfrom(1024)
			print('Reponse from ' + addr[0] + ' on port ' + str(addr[1]))	
			
			#parse response
			r = data_parser(resp)
			#get next address
			if(r['ANCOUNT'] == 0):
				address = r['authority0']['RDATA']
			else:
				answered = True
			#get cache expiry time
			if(answered):
				ttl = int(r['answer0']['TTL'])
			else:
				ttl = int(r['authority0']['TTL'])
			exp = int(time.time()) + ttl

			#make new cache entry
			cache[entry] = (resp, exp, address, answered)
	s.close()	
	return resp

def server(port_number):
	host = '127.0.0.1'
	port = port_number

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((host, port))

	print('Socket is listening..')

	#repeatedly take UDP requests
	while True:
		query, address = s.recvfrom(1024)
		resp = client(query)
		s.sendto(resp, address)

cache = {}
server(int(sys.argv[1]))
