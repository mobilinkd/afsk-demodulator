#!/bin/env python

from scipy.signal import lfiltic, lfilter, firwin
import numpy as np

class iir_filter(object):
    def __init__(self, b, a):
        self.b = b
        self.a = a
        self.zl = lfiltic(self.b, self.a, [], [])
    def __call__(self, data):
        result, self.zl = lfilter(self.b, self.a, [data], -1, self.zl)
        return result[0]

class Hysteresis:

    def __init__(self, minimum, maximum, low = -1, high = 1, start  = -1):

        self.minimum = minimum
        self.maximum = maximum
        self.low = low
        self.high = high
        self.value = start

    def check(self, value):
    
        if value <= self.minimum:
            self.value = self.low
        elif value >= self.maximum:
            self.value = self.high
        
        return self.value

    def __call__(self, data):

        try:
            return np.array([self.check(x) for x in data])
        except TypeError:
            return self.check(data)

class DigitalPLL:

    # 64Hz Bessel Filter for Loop
    loop_b = [
        0.144668495309,
        0.144668495309]
    
    loop_a  = [
        1.0,
        -0.710663009381]
    
    # 40Hz Bessel Filter for Lock
    lock_b = [
        0.0951079834025,
        0.0951079834025]
   
    lock_a  = [
        1.0,
        -0.809784033195]


    def __init__(self, sample_rate, symbol_rate):
        self.sample_rate_ = sample_rate
        self.symbol_rate_ = symbol_rate
        self.sps_ = sample_rate / symbol_rate   ##< Samples per symbol
        self.limit_ = self.sps_ / 2             ##< Samples per symbol / 2
        self.lock_ = Hysteresis(self.sps_ * 0.025, self.sps_ * 0.15, 1, 0)
        self.loop_lowpass = iir_filter(self.loop_b, self.loop_a)
        self.lock_lowpass = iir_filter(self.lock_b, self.lock_a)
    
        self.last_ = False
        self.count_ = 0.0
    
        self.sample_ = False
        self.jitter_ = 10.0
        self.bits_ = 1.0

    def __call__(self, input):
        
        self.sample_ = False;
        
        if (input != self.last_ or self.bits_ > 127.0):
            # Record transition.
            self.last_ = input

            if (self.count_ > self.limit_):
                self.count_ -= self.sps_
                        
            offset = self.count_ / self.bits_

            j = self.loop_lowpass(offset)
            self.jitter_ = self.lock_lowpass(abs(offset))
            
            # Advance or retard if not near a bit boundary.
            self.count_ -=  j * self.sps_ * (0.012 if self.locked() else 0.048)
            
            self.bits_ = 1.0
        else:
            if (self.count_ > self.limit_):
                self.sample_ = True
                self.count_ -= self.sps_
                self.bits_ += 1

        self.count_ += 1.0
        return self.sample_
    
    def locked(self):
        return self.lock_(self.jitter_)

    
    def jitter(self):
        return self.jitter_

