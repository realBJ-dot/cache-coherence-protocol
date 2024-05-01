"""
This file implements the ESI coherence protocol
"""


from base import *

class ESI(Coherence):
    def handle_l1_eviction(self, cpu_id: int, line: Line):
        # get current cache
        cache = self.l1_caches[cpu_id]
        # if line is dirty, write back to llc and mark it clean again
        if line.dirty:
            self.llc.update_data(cache.get_data(line.addr))
            cache.update_dirty(line.addr, False)

    def read(self, cpu_id: int, addr: int):
        # get cache from cpu id
        cache = self.l1_caches[cpu_id]
        if cache.contains(addr) == False:
            cache.add_line(self.llc.get_line(addr))
        # get current state of this cache addr
        state = cache.get_state(addr)
        # if state is invalid, there are two types of read: read and readx
        if state == State.I:
            # get the data I wanna read from
            tryread_data = self.llc.get_data(addr)
            is_read = 0
            # readx, loop thru all L1 caches
            for i in range(self.cpu_count):
                cache_i = self.l1_caches[i]
                # if ith L1 cache contains this addr
                if cache_i.contains(addr):
                    is_read = 1
                    # check if that cache has state E at this addr
                    if cache_i.get_state(addr) == State.E:
                        # check if this is dirty, if it is, we need to write it back to llc first,
                        # then read from llc to copy the data to current block
                        if cache_i.get_dirty(addr):
                            updated_data = cache_i.get_data(addr)
                            self.llc.update_data(addr, updated_data) 
                            cache.update_data(addr, updated_data)
                            cache.update_dirty(addr, False)
                            return updated_data
                        # else if it is a clean E state, we just copy it over, updating both as S
                        else:
                            cache_i.update_state(addr, State.S)
                            cache.update_state(addr, State.S)
                            cache.update_data(addr, tryread_data)
                            cache.update_dirty(addr, False)
                    return tryread_data
                    

            # for readx situation
            if is_read == 0:
                cache.update_state(addr, State.E)
                cache.update_data(addr, tryread_data)
                cache.update_dirty(addr, False)
                cache.update_last_used(addr)
            return cache.get_data(addr)

        # else if the current state is E, write back and mark clean
        else:
            cache.update_last_used(addr)
            return cache.get_data(addr)



    def write(self, cpu_id: int, addr: int, data: int):
        # cache = self.l1_caches[cpu_id]
        # state = cache.get_state(addr)
        # # if it is invalid state, we should mark dirty and invalidate all other holding the copy.
        # if state == State.I:
        #     cache.update_dirty(addr, True)
        #     for i in range(self.cpu_count):
        #         this_cache = self.l1_caches[i]
        #         if this_cache.contains(addr):
        #             if this_cache.get_state(addr) == State.E:
        #                 if this_cache.get_dirty(addr):
        #                     # if this cache is dirty, write back to llc
        #                     self.llc.update_data(addr, this_cache.get_data(addr))
        #                 this_cache.update_state(State.I)
        #     cache.update_data(addr, data)
        #     cache.update_state(addr, State.E)
        # elif state == State.E:
        #     cache.update_dirty(addr, True)
        #     cache.update_data(addr, data)
        # else:
        #     cache.update_dirty(addr, True)
        #     cache.update_state(addr, State.E)
        #     cache.update_data(addr, data)
        pass


