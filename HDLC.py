#!/usr/bin/python

import sys

from CRC import CRC16CCITT
from io import StringIO

class HDLC:

    SEARCH = 0
    HUNT = 1
    FRAME = 2

    FLAG = 0x7E
    ABORT = 0x7F
    IDLE = 0xFF
    
    BOGONS = [0xFF00, 0xFE00, 0x7F00]
    FRAME_ERRORS = [0xFF00, 0xFE00, 0xFC00, 0x7F00, 0x7E00]

    def __init__(self, passall = False, callback = None):
    
        self.passall = passall
        self.callback = callback
        self.reset()
        self.action = [self.search, self.hunt, self.do_frame]
    
    def reset(self):
    
        self.state = HDLC.SEARCH
        self.bits = 0
        self.ones = 0
        self.buffer = 0
        self.frame = StringIO()
        self.ready = False
        self.pll = False
    
    def __call__(self, bit, pll):
    
        result = None
        
        if not pll:
            if self.frame.tell() > 14 and self.passall:
                result = (self.crc(), self.frame.getvalue())
                # print "lost lock"
            self.reset()
        else:
            self.pll = pll
            result = self.process(bit)
            if result is not None:
                crc = result[0]
                self.reset()
                if crc != 0xf0b8 and not self.passall:
                    result = None
                else:
                    self.start_hunt()
        
        return result
    
    def framing(self): return self.state == HDLC.FRAME
    
    def _add_bit(self, bit):
    
        self.buffer >>= 1
        self.buffer |= (0x8000 * int(bit))
        self.bits += 1
        # print hex(self.buffer), self.bits, bit
    
    def _have_flag(self):
    
        return (self.buffer & 0xFF00) == 0x7E00
    
    def _have_bogon(self):
    
        return (self.buffer & 0xFF00) in HDLC.BOGONS
    
    def _have_frame_error(self):
    
        return (self.buffer & 0xFF00) in HDLC.FRAME_ERRORS
    
    def start_search(self):
        
        # print "search"
        self.state = HDLC.SEARCH
    
    def search(self, bit):
    
        self._add_bit(bit)
        if self._have_flag():
            self.start_hunt()
        return None

    def start_hunt(self):
    
        # print "hunt"
        self.state = HDLC.HUNT
        self.bits = 0
        self.buffer = 0

    def hunt(self, bit):
    
        self._add_bit(bit)
        if self.bits == 8:
            if self._have_flag(): self.start_hunt()
            elif self._have_bogon(): self.start_search()
            elif not self._have_frame_error(): self.start_frame()
            else: self.start_search()
        
        return None
    
    def start_frame(self):
    
        # sys.stdout.write("\rframe")
        # sys.stdout.flush()
        self.state = HDLC.FRAME
        self.frame = StringIO()
        self.ones = 0
        self.buffer &= 0xFF00
    
    def getchar(self):
    
        return chr(self.buffer & 0xFF)
    
    def consume_byte(self):
    
        self.buffer &= 0xFF00
        self.bits -= 8
    
    def consume_bit(self):
    
        tmp = (self.buffer & 0x7F) << 1
        
        self.buffer &= 0xFF00
        self.buffer |= tmp
        self.bits -= 1
    
    def do_frame(self, bit):
    
        result = None
        
        self._add_bit(bit)
        
        if self.ones < 5:
            if (self.buffer & 0x80) == 0x80:
                self.ones += 1
            else:
                self.ones = 0
        
            if self.bits == 16:
                self.frame.write(self.getchar())
                self.consume_byte()

            if self._have_flag():
                if self.frame.tell() > 14:
                    # result = self.check_frame()
                    result = (self.crc(), self.frame.getvalue()[:-2])
                self.start_frame()

        else: # too many ones
            if (self.buffer & 0x80) == 0:
                self.consume_bit()
                self.ones = 0
            else:
                # print "frame error"
                if self.passall and self.frame.tell() > 14:
                    result = (self.crc(), self.frame.getvalue())
                # Framing error
                if ((self.buffer >> (16 - self.bits)) & 0xFF) == 0x7E:
                    # Cannot call start_hunt(); we need to preserve buffer
                    self.bits -= 8
                    self.state = HDLC.HUNT
                    self.frame = StringIO()
                else:
                    self.start_search()
        
        return result

    def process(self, bit):
        
        return self.action[self.state](bit)
    
    def check_frame(self):
    
        if self.crc() == 0xF0B8: return self.frame.getvalue()
        return None
    
    def crc(self):
    
        crc = CRC16CCITT()
        return crc.compute(self.frame.getvalue())
    
