#!/usr/bin/env python
# encoding: utf-8
"""
ultradns.py

Created by Josh Rendek on 2009-06-23.
Copyright (c) 2009 Josh Rendek. All rights reserved.
Website: http://bluescripts.net/
"""

from OpenSSL import SSL
import sys, os, select, socket
try:
	from xml.etree import ElementTree as ET
except:
	import elementtree.ElementTree as ET
sponsor = "ultradnsweb"
username = "user"
password = "pw" #make sure its alphanumeric, signs like '&' will screw it up

class UDNS:
	def header(self): #header
		return "<?xml version=\"1.0\" ?><transaction>"
	def login(self,username, password, sponsor): #authorization request
		xml = "<methodCall>"
		xml += "<methodName>UDNS_OpenConnection</methodName>"
		xml += "<params>"
		xml += "<param><value><string>"+sponsor+"</string></value></param>"
		xml += "<param><value><string>"+username+"</string></value></param>"
		xml += "<param><value><string>"+password+"</string></value></param>" #make sure its alphanumeric, signs like '&' will screw it up
		xml += "<param><value><float>2.0</float></value></param>"
		xml += "</params>"
		xml += "</methodCall>"
		return xml
	
	def create_a_record(self, zone, host, ip): #creates an a record xml request
		xml = "<methodCall>"
		xml += "<methodName>UDNS_CreateARecord</methodName>"
		xml += "<params>"
		xml += "<param><value><zonename>"+zone.capitalize()+".</zonename></value></param>" #need trailing dot also first letter must be uppercase
		xml += "<param><value><hostname>"+host+".</hostname></value></param>" # need trailing dot again - example: test.example.com.
		xml += "<param><value><ip_address>"+ip+"</ip_address></value></param>" #regular ip
		xml += "</params>"
		xml += "</methodCall>"
		return xml
		
	def generic_call(self,methodName, params): #generic xml method creator
		#params is a list because dictionary doesnt return a set order, UltraDNS requires set order of params
		xml = "<methodCall><methodName>" + methodName + "</methodName>"
		xml += "<params>"
		for i in params:
			if i[0] == 'zonename': #checks for zonename which needs uppercase first letter and then adds a . at end
				i[1] = i[1].capitalize() + "."
			if i[0] == 'hostname': #checks for hostname, adds . at end for compliance
				i[1] = i[1] + "." 
			xml += "<param><value><"+i[0]+">"+i[1]+"</"+i[0]+"></value></param>"
		xml += "</params></methodCall>"
			
		return xml
		
	def respond(self,response): #human readable way to read the api response
		parse_response = ET.XML(response)
		p = parse_response.getiterator()
		for i in p:
				try:
					if i.tag == 'string':
						#print i.tag + " -> " + i.text
						print "Message from server: " + i.text
				except TypeError: #for when i.text doesn't exist
					#print i.tag + " -> no val"
					pass
	def debug_call(self,xml): #debug function, call on a trans to print out a human readable xml key,value pair
		print "----- DEBUG ----\n"
		parse_response = ET.XML(xml)
		p = parse_response.getiterator()
		for i in p:
				try:
					print i.tag + " -> " + i.text
				except TypeError:
					print i.tag + " -> noValue "	
		print "/----- DEBUG ----\n"

	def disconnect(self): #disconnect request
		xml = "<methodCall>"
		xml += "<methodName>UDNS_Disconnect</methodName>"
		xml += "</methodCall></transaction>"
		return xml

	def usage(self): #show help
		print "Usage: ./ultradns.py ACTION options"
		print "-- Generic Example: ./ultradns.py methodName param,value param2,value2 param3,value3"
		print "-- Example Options for UDNS_CreateARecord: zonename hostname ip"
		print "-- Options for import: /path/to/file"
		
		
		print "Example: ./ultradns.py UDNS_CreateARecord example.com subdomain.example.com 1.2.3.4"
		pass

#initialize ssl
ctx = SSL.Context(SSL.TLSv1_METHOD)
#init UDNS class
udns = UDNS()
#setup connection
sock = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM)) #open ssl socket connection
sock.connect(('api.ultradns.net', 8755)) #connect to the api server
print "Connected "
if len(sys.argv) <= 2: #check for usage errors in command
	udns.usage()
	sys.exit(2)

if sys.argv[1] != 'import': #for all other calls to the generic api function
	params = []
	for x in sys.argv: #loop through param,value pairs in command line to build xml
		try:
			l = x.split(',')
			params += [ [ l[0] , l[1]  ] ] #load up param,value pairs
		except IndexError:
			pass
	trans = udns.header() + udns.login(username,password,sponsor) + udns.generic_call('UDNS_CreateARecord', params) + udns.disconnect() #construct the full xml call

elif sys.argv[1] == 'import':
	file_to_open = open(sys.argv[2], 'r') #read in file
	header = file_to_open.readline().rstrip("\n").split(',') #strip new lines '\n' and then explode the ,
	i = 0 # set of transactions
	t = 0 # transaction counter
	for line in file_to_open: #read each line of file except header readline() already skipped the header part 
		if i == 0:
			print "Starting transaction"
			response = ""
			trans = udns.header() + udns.login(username,password,sponsor) #restart transaction xml for each 10 requests
			
		l = line.rstrip("\n").split(',')
		if header[0] == "UDNS_CreateARecord": # you can change this and add more checks in for other types of mass importing
			try:
				trans += udns.generic_call(header[0], [ ['zonename', header[1]], ['hostname', l[0]+"."+header[1]], ['ip_address', l[1]] ] )
				i+=1
			except IndexError: #out of index fix
				pass
		if i == 10: #break off, reset counter, execute transaction
			t+=1
			
			trans +=  udns.disconnect()
			try: #10 calls have been reached, execute transaction
				sock.send(trans)
			except SSL.SysCallError: 
				pass
			
			while 1: #loop through the response from api
				try:
					response += sock.recv(1024)
					#print sock.recv(1024)
				except SSL.ZeroReturnError:
					print '\n-------------\nNo More to Read Closing\n-------------\n'
					break
			
			udns.respond(response)
			i = 0
			""" really stupid error iwth SSL, you can only send 64kb of data before it errors, 
			solution for me is to disconnect then reconnect to the api socket
			see: http://rt.openssl.org/Ticket/Display.html?id=598&user=guest&pass=guest """
			sock.shutdown()
			sock.close()
			print "Ending transaction set ", t
			print "\n\n"
			sock = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
			sock.connect(('api.ultradns.net', 8755))
			
#readback output
if sys.argv[1] != 'import':
	print "Transaction built"

	print "Transaction sent"
	response = ""

	print "Reading response"


	# debug xml sent
	#udns.debug_call(trans)
	
	sock.send(trans)
	while 1: #loop through the received data from api
		try:
			response += sock.recv(1024)
			#print sock.recv(1024)
		except SSL.ZeroReturnError:
			print '\n-------------\nNo More to Read Closing\n-------------\n'
			break	
	udns.respond(response)
	
	sys.stdout.flush()

	#finish up, it may take a minute or two for it to showup in the records on the site admin panel
	sock.shutdown()
	sock.close()

