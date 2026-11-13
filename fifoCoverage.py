import vsc

FIFO_DEPTH = 8

@vsc.covergroup
class FifoCoverage(object):
    def __init__(self):
        # Values passed to sample(), in this order
        self.with_sample(dict(
            count=vsc.uint8_t(),   # PRE-edge occupancy
            wr_en=vsc.bit_t(1),
            rd_en=vsc.bit_t(1),
            rst_n=vsc.bit_t(1),
        ))

        # Occupancy: one bin per level (fills the occupancy table, C9/C12)
        self.cp_occ = vsc.coverpoint(
            self.count,
            bins={f"occ_{i}": vsc.bin(i) for i in range(FIFO_DEPTH + 1)}
        )

        # FIFO state: empty / mid / full (C2, C3, C6, C7)
        self.cp_state = vsc.coverpoint(
            self.count,
            bins=dict(
                empty=vsc.bin(0),
                mid=vsc.bin([1, FIFO_DEPTH - 1]),
                full=vsc.bin(FIFO_DEPTH),
            )
        )

        self.cp_wr = vsc.coverpoint(self.wr_en, bins=dict(off=vsc.bin(0), on=vsc.bin(1)))
        self.cp_rd = vsc.coverpoint(self.rd_en, bins=dict(off=vsc.bin(0), on=vsc.bin(1)))
        self.cp_rst = vsc.coverpoint(self.rst_n, bins=dict(asserted=vsc.bin(0), released=vsc.bin(1)))

        # X2 / section 8: op x state. 2x2x3 = 12 bins, including the
        # undefined/illegal combos (rd+wr at empty, rd+wr at full, wr at full, rd at empty)
        self.cross_op_state = vsc.cross([self.cp_wr, self.cp_rd, self.cp_state])

        # C1 / section 8: reset asserted in each state, with and without traffic
        self.cross_rst_state = vsc.cross([self.cp_rst, self.cp_state, self.cp_wr, self.cp_rd])

fifo_cov = FifoCoverage()