"""
This file implements the ESI coherence protocol
"""


from base import *

class ESI(Coherence):
    def handle_l1_eviction(self, cpu_id: int, line: Line):
        pass

    def read(self, cpu_id: int, addr: int):
        pass

    def write(self, cpu_id: int, addr: int, data: int):
        pass
