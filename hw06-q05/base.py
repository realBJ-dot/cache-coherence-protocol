"""
THIS FILE IS NOT GRADED.

This file defines the base types used in the homework.
"""

import copy
import math
import sys
import yaml

from abc import ABC, abstractmethod
from collections import OrderedDict
from enum import Enum
from typing import List

class BaseState(Enum):
    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, short: str, sharers: bool, dirty: bool, valid: bool):
        self._short = short
        self._sharers = sharers
        self._dirty = dirty
        self._valid = valid

    def __str__(self):
        return self.value

    @property
    def dirty(self):
        return self._dirty

    @property
    def valid(self):
        return self._valid

    @property
    def sharers(self):
        return self._sharers


class State(BaseState):
    M = "M", False, True, True
    E = "E", False, False, True
    S = "S", True, False, True
    I = "I", False, False, False


class StatePropert:
    sharers = None
    valid = None
    dirty = None

    def __init__(self, sharers=False, valid=False, dirty=False):
        self.sharers = sharers
        self.valid = valid
        self.dirty = dirty


class Line:
    addr: int
    state: State
    last_used: int
    data: int
    dirty: bool

    def __init__(self, addr: int, data: int, last_used: int):
        self.addr = addr
        self.state = None
        self.last_used = last_used
        self.data = data
        self.dirty = False
    
    def update_dirty(self, dirty: bool):
        self.dirty = dirty

    def update_state(self, state: State):
        self.state = state

    def update_last_used(self, last_used: int):
        self.last_used = last_used

    def get_dict(self):
        if self.state is None:
            return {
                "addr": self.addr,
                "data": self.data,
            }
        if self.state.valid == False:
             return {"addr": self.addr, "state": self.state._short}
        return {"addr": self.addr, "data": self.data, "state": self.state._short, "last_used": self.last_used, "dirty" : self.dirty}


class Clock:
    _clk: int

    def __init__(self):
        self._clk = 0

    def tick(self):
        self._clk += 1

    def get_clock(self):
        return self._clk


clock = Clock()


class Coherence(ABC):
    l1_caches = list()
    llc = None
    cpu_count = 0

    def __init__(self, cpu_count: int, l1_size: int, def_enums=True):
        self.l1_caches = [L1(l1_size, self, i) for i in range(cpu_count)]
        self.llc = LLC(math.inf, None, -1)
        self.cpu_count = cpu_count

    @abstractmethod
    def handle_l1_eviction(self, cpu_id: int, line: Line):
        pass

    @abstractmethod
    def read(self, cpu_id: int, addr: int):
        pass

    @abstractmethod
    def write(self, cpu_id: int, addr: int, data: int):
        pass


class Cache(ABC):
    _data = None
    _size = 0
    _curr_size = 0
    _coherence = None
    _id = -1

    def __init__(self, size: int, coherence: Coherence, cache_id: int):
        self._data = OrderedDict()
        self._size = size
        self._curr_size = 0
        self._coherence = coherence
        self._id = cache_id

    def add_line(self, line: Line):
        if self._curr_size == self._size:
            self.evict()
        line_duplicate = copy.deepcopy(line)
        self._data[line_duplicate.addr] = line_duplicate
        self._curr_size += 1

    def contains(self, addr: int):
        return addr in self._data

    @abstractmethod
    def handle_eviction(self, line: Line):
        pass

    @abstractmethod
    def get_line(self, addr: int):
        pass

    def get_state(self, addr: int):
        if addr not in self._data:
            print(f"cannot get {addr} as it is not in cache")
            sys.exit(1)
        return self._data[addr].state
    
    def get_dirty(self, addr: int):
        if addr not in self._data:
            print(f"cannot get {addr} as it is not in cache")
            sys.exit(1)
        return self._data[addr].dirty

    def get_data(self, addr: int):
        if addr not in self._data:
            print(f"cannot get {addr} as it is not in cache")
            sys.exit(1)
        return self._data[addr].data

    def update_line(self, line: Line):
        if line.addr not in self._data:
            print(f"llc store does not contain data for {line.addr}")
            sys.exit(1)
        line_duplicate = copy.deepcopy(line)
        self._data[line.addr] = line_duplicate

    def update_state(self, addr: int, state: State):
        if addr not in self._data:
            print(f"updating state of line {addr} not in cache")
            sys.exit(1)
        self._data[addr].state = copy.deepcopy(state)
    
    def update_dirty(self, addr: int, dirty: bool):
        if addr not in self._data:
            print(f"updating state of line {addr} not in cache")
            sys.exit(1)
        self._data[addr].dirty = dirty

    def update_data(self, addr: int, data: int):
        if addr not in self._data:
            print(f"updating state of line {addr} not in cache")
            sys.exit(1)
        self._data[addr].data = data

    def update_last_used(self, addr: int):
        if addr not in self._data:
            print(f"updating last used of line {addr} not in cache")
            sys.exit(1)
        self._data[addr].last_used = clock.get_clock()

    def evict(self):
        if self._curr_size < self._size:
            return
        if self._curr_size == 0:
            return
        last_used_line = Line(-1, 0, math.inf)
        for addr in self._data:
            if self._data[addr].last_used < last_used_line.last_used:
                last_used_line = copy.deepcopy(self._data[addr])
        if last_used_line.addr == -1 or last_used_line.addr not in self._data:
            print("eviction failed: couldn't find any line to evict")
            sys.exit(1)
        evicted_line = copy.deepcopy(last_used_line)
        self._data.pop(last_used_line.addr)
        self._curr_size -= 1
        self.handle_eviction(evicted_line)


class LLC(Cache):
    _writebacks = 0

    def get_line(self, addr: int):
        if addr not in self._data:
            self._data[addr] = Line(addr, 0, -1)
        line_duplicate = copy.deepcopy(self._data[addr])
        return line_duplicate

    def handle_eviction(self, line: Line):
        print("infinite llc should not have evictions")
        sys.exit(1)

    def update_line(self, line: Line):
        if line.addr not in self._data:
            print(f"llc store does not contain data for {line.addr}")
            sys.exit(1)
        line_duplicate = copy.deepcopy(line)
        line_duplicate.state = None
        line_duplicate.dirty = False
        self._data[line.addr] = line_duplicate
        self._writebacks += 1

    def add_line(self, line: Line):
        print("llc is inclusive and you shouldn't add data to it")
        sys.exit(1)
    
    def update_data(self, addr: int, data: int):
        if addr not in self._data:
            print(f"updating state of line {addr} not in cache")
            sys.exit(1)
        self._data[addr].data = data
        self._writebacks += 1


class L1(Cache):
    def handle_eviction(self, line: Line):
        if self._coherence is None:
            print("coherence object for l1 cache is none")
            sys.exit(1)
        self._coherence.handle_l1_eviction(self._id, line)
    
    def get_line(self, addr: int):
        if addr not in self._data:
            print(f"cannot get {addr} as it is not in cache")
            sys.exit(1)
        line_duplicate = copy.deepcopy(self._data[addr])
        return line_duplicate