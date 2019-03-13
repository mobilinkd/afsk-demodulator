#!/bin/env python

from curses.ascii import isprint

class AX25:

	def __init__(self, frame):
		
		self.frame = frame
		self.dest = ''
		self.source = ''
		self.pid = 0
		self.repeaters = []
		self.info = ''
		self.parse(frame)
	
	def parse(self, frame):
	
		self.parse_destination(frame)
		has_repeaters = self.parse_source(frame)
		pos = 14
		if has_repeaters:
			pos = self.parse_repeaters(frame)
		
		if pos >= len(frame): return
		
		pos = self.parse_type(frame, pos)
		self.parse_info(frame, pos + 1)
	
	def printable(self, c):
	
		if isprint(c): return c
		else: return '?'
	
	def fixup_address(self, addr):
	
		more = (ord(addr[-1]) & 1) == 0;

		ssid = ord(addr[-1]) & 0x0F
		tmp = "".join([self.printable(chr(ord(x)>>1)) for x in addr[:-1]]).split(" ", 1)[0]
		if ssid != 0:
			result = tmp + ("-%d" % ssid)
		else:
			result = tmp
		return (more, result)
	
	def parse_destination(self, frame):
		
		result, self.dest = self.fixup_address(frame[0:7])
		return result
	
	def parse_source(self, frame):
	
		result, self.source = self.fixup_address(frame[7:14])
		return result
	
	def parse_repeaters(self, frame):
	
		pos = 14
		while True:
			more, repeater = self.fixup_address(frame[pos:pos + 7])
			pos += 7
			self.repeaters.append(repeater)
			if not more or pos > len(frame): break
		
		return pos
	
	def parse_type(self, frame, pos):
	
		self.pid = ord(frame[pos]) & 3
		return pos + 1
	
	def parse_info(self, frame, pos):
	
		self.info = "".join([self.printable(x) for x in frame[pos:]])
	
	def __str__(self):
	
		return "%s>%s,%s:%s" % (self.source, self.dest, ",".join(self.repeaters), self.info)

		
			
	
